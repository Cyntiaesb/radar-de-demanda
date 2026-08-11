"""Mercado Livre BR — produtos com volume real de venda.

Killer feature: enquanto Google e Reddit medem INTENÇÃO,
Mercado Livre mede COMPRA EFETIVA. Se tem 200 anúncios do produto X
com mil vendidos, dor é real e tem dinheiro circulando.

API pública gratuita, sem auth: https://api.mercadolibre.com/sites/MLB/search

Uso:
    from cookia.fontes.mercado_livre import buscar_produtos
    out = buscar_produtos(["curso produtividade", "mentoria"], limit=20)
"""
from __future__ import annotations
import time
from typing import Iterable

import httpx

ML_SEARCH = "https://api.mercadolibre.com/sites/MLB/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CookiaBot/1.0)",
    "Accept": "application/json",
}


def _fetch(query: str, limit: int = 20, offset: int = 0) -> dict | None:
    params = {"q": query, "limit": limit, "offset": offset}
    try:
        with httpx.Client(timeout=12.0, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(ML_SEARCH, params=params)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"      [ml] HTTP {r.status_code} pra '{query}': {r.text[:120]}")
    except httpx.HTTPError as e:
        print(f"      [ml] erro de rede pra '{query}': {e}")
    return None


def _normaliza(hit: dict, query: str) -> dict:
    return {
        "texto": hit.get("title", "").strip(),
        "fonte": "mercado_livre",
        "url": hit.get("permalink") or "",
        "metadata": {
            "query": query,
            "preco": hit.get("price"),
            "moeda": hit.get("currency_id"),
            "vendidos": hit.get("sold_quantity"),
            "categoria": hit.get("category_id"),
            "condicao": hit.get("condition"),
            "tipo_anuncio": hit.get("listing_type_id"),
            "envio_gratis": hit.get("shipping", {}).get("free_shipping"),
            "tipo": "produto_comercializado",
        },
    }


def buscar_produtos(queries: Iterable[str], *, limit: int = 20, delay: float = 0.5) -> list[dict]:
    """Busca produtos no ML BR. Retorna lista de sinais no schema Cookia.

    Vendidos (sold_quantity) é nossa proxy de DEMANDA EFETIVA.
    """
    out: list[dict] = []
    visto: set[str] = set()

    for q in queries:
        print(f"  🛒 ml: {q}")
        data = _fetch(q, limit=limit)
        if not data:
            continue

        for hit in data.get("results", []):
            sinal = _normaliza(hit, q)
            chave = sinal["url"] or sinal["texto"][:80]
            if chave in visto:
                continue
            visto.add(chave)
            out.append(sinal)
        time.sleep(delay)

    return out


def estatisticas_categoria(queries: Iterable[str]) -> dict:
    """Agrega métricas pra entender saturação do nicho:
       - preço médio
       - top vendidos (qtd)
       - quantos anúncios competem
    """
    todos = buscar_produtos(queries, limit=30)
    if not todos:
        return {"total": 0, "saturacao": "indefinida"}

    precos = [s["metadata"]["preco"] for s in todos if s["metadata"].get("preco")]
    vendidos = [s["metadata"]["vendidos"] or 0 for s in todos]

    return {
        "total_anuncios_amostra": len(todos),
        "preco_medio": round(sum(precos) / len(precos), 2) if precos else None,
        "preco_min": min(precos) if precos else None,
        "preco_max": max(precos) if precos else None,
        "total_vendidos_amostra": sum(vendidos),
        "top_vendido": max(vendidos) if vendidos else 0,
        "saturacao": "alta" if len(todos) >= 25 else "media" if len(todos) >= 10 else "baixa",
    }


if __name__ == "__main__":
    import json, sys
    queries = sys.argv[1:] or ["curso produtividade"]
    print(json.dumps(buscar_produtos(queries, limit=10), ensure_ascii=False, indent=2))
