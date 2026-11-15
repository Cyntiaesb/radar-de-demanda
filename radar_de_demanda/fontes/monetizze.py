"""Monetizze Vitrine de Afiliação — 35mil+ produtos, ~450k acessos/mês.

Diferente da Hotmart (busca pública sem login), a vitrine da Monetizze só é
acessível de dentro do painel logado (Menu > Vitrine de afiliação, confirmado
na central de ajuda oficial) — não existe endpoint público pra scraping
automático. Este módulo só gera o link de login certo pra abrir manualmente
e buscar o termo lá dentro (a vitrine tem busca por nome/categoria/comissão/
preço uma vez logado).

Uso:
    from radar_de_demanda.fontes.monetizze import buscar_infoprodutos
    out = buscar_infoprodutos(["emagrecimento"])
"""
from __future__ import annotations
from typing import Iterable

MARKETPLACE_URL = "https://app.monetizze.com.br/login"


def build_search_url(query: str) -> str:
    """Vitrine exige login e não aceita busca via query string pública.

    Retorna a URL de login — abrir logado e buscar `query` na Vitrine de afiliação.
    """
    return MARKETPLACE_URL


def buscar_infoprodutos(queries: Iterable[str], *, limit: int = 15, delay: float = 1.0) -> dict:
    """Sempre retorna scraping_funcionou=False — Monetizze exige login, sem API pública.

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
