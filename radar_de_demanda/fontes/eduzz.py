"""Eduzz Vitrine Select — infoprodutos disponíveis pra afiliação na Eduzz.

Diferente da Hotmart (busca pública sem login), a Vitrine Select só é
acessível de dentro do painel logado da Eduzz — não existe endpoint público
pra scraping automático. Este módulo só gera o link de login certo pra abrir
manualmente e buscar o termo lá dentro.

Uso:
    from cookia.fontes.eduzz import buscar_infoprodutos
    out = buscar_infoprodutos(["emagrecimento"])
"""
from __future__ import annotations
from typing import Iterable

MARKETPLACE_URL = "https://my.eduzz.com/user"


def build_search_url(query: str) -> str:
    """Vitrine Select exige login e não aceita busca via query string pública.

    Retorna a URL de login — abrir logado e buscar `query` na Vitrine Select.
    """
    return MARKETPLACE_URL


def buscar_infoprodutos(queries: Iterable[str], *, limit: int = 15, delay: float = 1.0) -> dict:
    """Sempre retorna scraping_funcionou=False — Eduzz exige login, sem API pública.

    Returns:
        {"produtos": [], "urls_busca": [{"query", "url"}], "scraping_funcionou": False}
    """
    urls = [{"query": q, "url": build_search_url(q)} for q in queries]
    return {"produtos": [], "urls_busca": urls, "scraping_funcionou": False}


if __name__ == "__main__":
    import json
    import sys
    queries = sys.argv[1:] or ["emagrecimento"]
    print(json.dumps(buscar_infoprodutos(queries), ensure_ascii=False, indent=2))
