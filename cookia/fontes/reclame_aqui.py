"""Scraper de Reclame Aqui — extrai reclamações como sinais de OBJEÇÃO.

Foco: pegar o título + corpo da reclamação. Ranqueado por relevância.

Cada sinal: {"texto": str, "fonte": "reclame_aqui", "url": str, "metadata": dict}

Uso:
    from cookia.fontes.reclame_aqui import scrape_reclame_aqui
    sinais = scrape_reclame_aqui(["advocacia", "honorários"], max_per_query=20)
"""
from __future__ import annotations
import time
from typing import Iterable
from urllib.parse import quote_plus

import httpx

# Endpoint público de busca (server-side). Não exige auth, mas tem rate-limit.
SEARCH_API = "https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/query/complains"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CookiaBot/1.0; demand-intel)",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://www.reclameaqui.com.br/",
}


def _fetch(query: str, page: int = 0, size: int = 20, retries: int = 2) -> list[dict]:
    """Busca reclamações via API pública. Retorna lista crua de hits."""
    params = {
        "query": query,
        "page": page,
        "size": size,
        "source": "complains",
    }
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=15.0, headers=HEADERS) as client:
                r = client.get(SEARCH_API, params=params)
            if r.status_code == 200:
                data = r.json()
                return data.get("complains", []) or data.get("hits", []) or []
            if r.status_code == 429:
                time.sleep(2.0 * (attempt + 1))
                continue
            return []
        except (httpx.HTTPError, ValueError) as e:
            if attempt == retries:
                print(f"    ⚠ RA falhou pra '{query}': {e}")
                return []
            time.sleep(1.0)
    return []


def _normaliza(hit: dict) -> dict | None:
    """Converte hit cru da API em sinal padrão Cookia."""
    titulo = (hit.get("title") or hit.get("titulo") or "").strip()
    corpo = (hit.get("description") or hit.get("descricao") or hit.get("body") or "").strip()
    if not (titulo or corpo):
        return None

    texto = f"{titulo}\n\n{corpo}".strip() if corpo else titulo

    rid = hit.get("id") or hit.get("complainId") or ""
    slug = hit.get("url") or hit.get("permalink") or ""
    url = slug if slug.startswith("http") else f"https://www.reclameaqui.com.br/{slug.lstrip('/')}" if slug else f"https://www.reclameaqui.com.br/busca/?q={rid}"

    return {
        "texto": texto,
        "fonte": "reclame_aqui",
        "url": url,
        "metadata": {
            "id": str(rid),
            "empresa": hit.get("company") or hit.get("companyName") or hit.get("empresa"),
            "status": hit.get("status"),
            "data": hit.get("created") or hit.get("creationDate") or hit.get("data"),
            "tipo": "objecao",
        },
    }


def scrape_reclame_aqui(
    queries: Iterable[str],
    *,
    max_per_query: int = 20,
    delay: float = 1.2,
) -> list[dict]:
    """Roda busca multi-query no Reclame Aqui BR.

    Args:
        queries: termos a buscar (geralmente seeds do nicho)
        max_per_query: limite de reclamações por termo
        delay: pausa entre queries (respeita rate-limit)

    Returns:
        lista de sinais normalizados (deduplicados por id)
    """
    out: list[dict] = []
    visto: set[str] = set()

    for q in queries:
        print(f"  🔍 RA query: {q}")
        hits = _fetch(q, page=0, size=max_per_query)
        for hit in hits:
            sinal = _normaliza(hit)
            if sinal is None:
                continue
            sid = sinal["metadata"]["id"] or sinal["texto"][:80]
            if sid in visto:
                continue
            visto.add(sid)
            out.append(sinal)
        time.sleep(delay)

    print(f"  ✓ {len(out)} reclamações extraídas")
    return out


if __name__ == "__main__":
    import json, sys
    queries = sys.argv[1:] or ["advocacia"]
    result = scrape_reclame_aqui(queries, max_per_query=5)
    print(json.dumps(result[:3], ensure_ascii=False, indent=2))
