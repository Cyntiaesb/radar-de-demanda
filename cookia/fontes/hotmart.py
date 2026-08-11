"""Hotmart Marketplace — captura infoprodutos VENDENDO no Brasil.

Killer feature pra infoproductor: Hotmart é onde o jogo acontece.
Mercado Livre captura curso/ebook mas o ECOSSISTEMA INFOPRODUTO é Hotmart.

Estratégia defensiva (graceful degradation):
  1. Tenta endpoint público de busca da Hotmart
  2. Parsea HTML em busca de products embedded
  3. Se falhar: retorna URLs prontas pro cliente abrir manualmente
"""
from __future__ import annotations
import json
import re
import time
from typing import Iterable
from urllib.parse import quote_plus

import httpx

HOTMART_SEARCH_HTML = "https://hotmart.com/pt-br/marketplace/produtos"
HOTMART_SEARCH_API = "https://api-marketplace.hotmart.com/api/v1/marketplace/products"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://hotmart.com/pt-br/marketplace",
}


def build_search_url(query: str) -> str:
    """Gera URL pública de busca da Hotmart filtrada por keyword."""
    return f"{HOTMART_SEARCH_HTML}?q={quote_plus(query)}"


def _tenta_api(query: str, limit: int = 20) -> list[dict] | None:
    """Tenta endpoint não-oficial. Retorna None se falhar."""
    params = {"q": query, "size": limit, "page": 0}
    try:
        with httpx.Client(timeout=12.0, headers=HEADERS) as c:
            r = c.get(HOTMART_SEARCH_API, params=params)
        if r.status_code == 200:
            data = r.json()
            return data.get("items") or data.get("products") or data.get("content") or []
    except (httpx.HTTPError, ValueError):
        return None
    return None


def _tenta_html(query: str) -> list[dict] | None:
    """Tenta scraping da página de busca. HTML pode estar JS-rendered (limitação)."""
    url = build_search_url(query)
    try:
        with httpx.Client(timeout=12.0, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(url)
        if r.status_code != 200:
            return None
        html = r.text
    except httpx.HTTPError:
        return None

    produtos = []

    # Tentativa 1: JSON-LD schema.org embarcado
    for m in re.finditer(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL):
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, dict) and data.get("@type") in ("Product", "Course"):
                produtos.append({
                    "name": data.get("name"),
                    "price": data.get("offers", {}).get("price") if isinstance(data.get("offers"), dict) else None,
                    "rating": data.get("aggregateRating", {}).get("ratingValue") if isinstance(data.get("aggregateRating"), dict) else None,
                    "url": data.get("url"),
                })
        except json.JSONDecodeError:
            continue

    # Tentativa 2: padrões de produto em JSON inline
    if not produtos:
        for m in re.finditer(r'"productName":"([^"]+)".*?"price":\s*([\d.]+)', html):
            produtos.append({
                "name": m.group(1),
                "price": float(m.group(2)),
            })

    return produtos if produtos else None


def _normaliza(hit: dict, query: str) -> dict:
    nome = hit.get("name") or hit.get("productName") or hit.get("title") or ""
    preco = hit.get("price") or hit.get("priceValue")
    if isinstance(preco, str):
        try:
            preco = float(preco.replace(",", "."))
        except ValueError:
            preco = None

    return {
        "texto": nome.strip(),
        "fonte": "hotmart",
        "url": hit.get("url") or hit.get("productUrl") or build_search_url(query),
        "metadata": {
            "query": query,
            "preco": preco,
            "rating": hit.get("rating") or hit.get("aggregateRating"),
            "formato": hit.get("type") or "infoproduto",
            "vendido": hit.get("salesCount") or hit.get("totalSales"),
            "tipo": "infoproduto",
        },
    }


def buscar_infoprodutos(queries: Iterable[str], *, limit: int = 15, delay: float = 1.0) -> dict:
    """Tenta capturar infoprodutos Hotmart pros termos. SEMPRE retorna URLs prontas.

    Returns:
        {
          "produtos": [...],          # pode ser [] se Hotmart bloqueou
          "urls_busca": [{"query", "url"}],  # SEMPRE preenchido
          "scraping_funcionou": bool
        }
    """
    produtos: list[dict] = []
    urls: list[dict] = []
    visto: set[str] = set()

    for q in queries:
        print(f"  🛒 hotmart: {q}")
        urls.append({"query": q, "url": build_search_url(q)})

        # Tentativa API primeiro, depois HTML
        hits = _tenta_api(q, limit=limit)
        if hits is None or len(hits) == 0:
            hits = _tenta_html(q) or []

        for hit in hits:
            produto = _normaliza(hit, q)
            chave = produto["texto"][:80]
            if chave and chave not in visto:
                visto.add(chave)
                produtos.append(produto)

        time.sleep(delay)
        if len(produtos) >= 50:
            break

    return {
        "produtos": produtos,
        "urls_busca": urls,
        "scraping_funcionou": len(produtos) > 0,
    }


if __name__ == "__main__":
    import sys
    queries = sys.argv[1:] or ["emagrecimento"]
    out = buscar_infoprodutos(queries, limit=10)
    print(json.dumps(out, ensure_ascii=False, indent=2)[:3000])
