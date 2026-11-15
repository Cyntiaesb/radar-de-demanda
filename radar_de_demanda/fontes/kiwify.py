"""Kiwify Marketplace — infoprodutos validados (R$5.000+ em vendas pra entrar na vitrine).

Diferente da Hotmart (busca pública sem login), o marketplace da Kiwify só é
acessível de dentro do painel logado (`dashboard.kiwify.com.br/marketplace`).
Não existe endpoint público pra scraping automático — este módulo só gera o
link certo pra abrir manualmente (logado na própria conta) e buscar o termo
lá dentro.

Sinal forte mesmo sem automação: só entra na vitrine quem já vendeu R$5.000+,
com taxa de reembolso <15% e chargeback <3% — é praticamente um "top produtos
validados" pronto.

Uso:
    from radar_de_demanda.fontes.kiwify import buscar_infoprodutos
    out = buscar_infoprodutos(["emagrecimento"])
"""
from __future__ import annotations
from typing import Iterable

MARKETPLACE_URL = "https://dashboard.kiwify.com.br/marketplace/"


def build_search_url(query: str) -> str:
    """Marketplace exige login e não aceita busca via query string pública.

    Retorna a URL do painel — abrir logado e buscar `query` lá dentro.
    """
    return MARKETPLACE_URL


def buscar_infoprodutos(queries: Iterable[str], *, limit: int = 15, delay: float = 1.0) -> dict:
    """Sempre retorna scraping_funcionou=False — Kiwify exige login, sem API pública.

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
