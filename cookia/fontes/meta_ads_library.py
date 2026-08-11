"""Meta Ads Library — scraping da biblioteca pública de anúncios da Meta.

Killer feature: anúncio RODANDO HOJE = oferta validada com dinheiro real.
Se a marca paga pra rodar há +30 dias, a oferta tá pagando ela mesma.

Estratégia em camadas (com graceful degradation):
  1. Tenta fetch direto da página pública (HTML com JSON embedded)
  2. Extrai metadados de anúncios via regex/json parsing
  3. Se falhar: retorna URLs prontas pro cliente abrir manualmente

URLs de busca pública: https://www.facebook.com/ads/library/
"""
from __future__ import annotations
import json
import re
import time
from datetime import datetime
from typing import Iterable
from urllib.parse import quote_plus, urlencode


_MESES = {"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,
          "jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12}


def _parse_dias_rodando(start_str: str | None) -> int | None:
    """Converte data de início ('Jan 15, 2026' ou '15 de jan de 2026') em dias até hoje."""
    if not start_str:
        return None
    s = start_str.strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return (datetime.now() - datetime.strptime(s, fmt)).days
        except ValueError:
            continue
    m = re.search(r"(\d{1,2})\s*(?:de\s*)?([a-zç]+)\s*(?:de\s*)?(\d{4})", s.lower())
    if m:
        dia, mes_txt, ano = m.groups()
        for k, v in _MESES.items():
            if mes_txt.startswith(k):
                try:
                    return (datetime.now() - datetime(int(ano), v, int(dia))).days
                except ValueError:
                    return None
    return None


import httpx

ADS_LIBRARY_BASE = "https://www.facebook.com/ads/library/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def build_search_url(keyword: str, *, country: str = "BR", active_only: bool = True) -> str:
    """Gera URL pública da Biblioteca de Anúncios filtrada por keyword + país."""
    params = {
        "active_status": "active" if active_only else "all",
        "ad_type": "all",
        "country": country,
        "q": keyword,
        "search_type": "keyword_unordered",
        "media_type": "all",
    }
    return f"{ADS_LIBRARY_BASE}?{urlencode(params, quote_via=quote_plus)}"


def _extrai_anuncios_html(html: str) -> list[dict]:
    """Tenta extrair anúncios do HTML embarcado da página da biblioteca.

    Meta serializa muito conteúdo em JSON dentro de <script> tags.
    Procura por padrões conhecidos.
    """
    anuncios = []

    # Padrão 1: textos curtos de anúncio aparecem como "body":{"text":"..."}
    bodies = re.findall(r'"body":\{"text":"([^"]{20,500})"', html)
    # Padrão 2: page_name
    pages = re.findall(r'"page_name":"([^"]{2,80})"', html)
    # Padrão 3: dias rodando — start_date_string
    starts = re.findall(r'"start_date_string":"([^"]+)"', html)
    # Padrão 4: link da landing
    links = re.findall(r'"link_url":"(https?://[^"]+)"', html)

    n = min(len(bodies), 30)
    for i in range(n):
        start = starts[i] if i < len(starts) else None
        dias = _parse_dias_rodando(start)
        anuncios.append({
            "texto": bodies[i].replace("\\n", " ").replace("\\/", "/").strip(),
            "pagina": pages[i] if i < len(pages) else "?",
            "comecou_em": start or "?",
            "dias_rodando": dias,
            "landing": links[i] if i < len(links) else None,
        })
    return anuncios


def tenta_fetch_anuncios(keyword: str, *, country: str = "BR", timeout: float = 12.0) -> list[dict]:
    """Tenta puxar anúncios ativos pro keyword. Retorna lista (pode ser vazia).

    Não falha — se Meta bloquear ou retornar HTML JS-rendered sem JSON, devolve [].
    """
    url = build_search_url(keyword, country=country)
    try:
        with httpx.Client(timeout=timeout, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(url)
        if r.status_code != 200:
            return []
        return _extrai_anuncios_html(r.text)
    except httpx.HTTPError:
        return []


def espiona_nicho(keywords: Iterable[str], *, country: str = "BR", max_total: int = 30, delay: float = 1.0) -> dict:
    """Pra cada keyword, tenta puxar anúncios + sempre retorna URL pública pronta.

    Returns:
        {
          "anuncios_extraidos": [...],   # pode ser [] se Meta bloqueou
          "urls_busca": [{"keyword", "url"}],  # SEMPRE preenchido — cliente abre manual
          "scraping_funcionou": bool
        }
    """
    todos: list[dict] = []
    urls_busca: list[dict] = []

    for kw in keywords:
        print(f"  🕵️  meta-ads: {kw}")
        url = build_search_url(kw, country=country)
        urls_busca.append({"keyword": kw, "url": url})

        ads = tenta_fetch_anuncios(kw, country=country)
        for ad in ads:
            ad["keyword_busca"] = kw
            todos.append(ad)
        if len(todos) >= max_total:
            break
        time.sleep(delay)

    visto = set()
    deduplicados = []
    for ad in todos:
        chave = ad.get("texto", "")[:100] + ad.get("pagina", "")
        if chave not in visto and ad.get("texto"):
            visto.add(chave)
            deduplicados.append(ad)

    return {
        "anuncios_extraidos": deduplicados[:max_total],
        "urls_busca": urls_busca,
        "scraping_funcionou": len(deduplicados) > 0,
    }


if __name__ == "__main__":
    import sys
    kws = sys.argv[1:] or ["emagrecimento"]
    out = espiona_nicho(kws)
    print(json.dumps(out, ensure_ascii=False, indent=2)[:3000])
