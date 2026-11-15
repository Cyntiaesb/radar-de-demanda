"""Links de busca para abrir à mão quando uma fonte fica indisponível.

Algumas fontes bloqueiam coleta automática (anti-robô, login, limite de
pedidos). O Radar não tenta contornar bloqueio: quando a fonte falha, o
dossiê entrega o link da busca pronta para a pessoa abrir no navegador.
"""
from __future__ import annotations
from typing import Iterable
from urllib.parse import quote, quote_plus

from .meta_ads_library import build_search_url as _meta_url

NOMES = {
    "google_autocomplete": "Google Autocomplete",
    "reddit": "Reddit",
    "reclame_aqui": "Reclame Aqui",
    "mercado_livre": "Mercado Livre",
    "youtube_comments": "Comentários do YouTube",
    "google_trends": "Google Trends",
    "meta_ads": "Biblioteca de Anúncios da Meta",
}


def _ml(q: str) -> str:
    return "https://lista.mercadolivre.com.br/" + quote(q.strip().replace(" ", "-"))


_BUILDERS = {
    "google_autocomplete": lambda q: f"https://www.google.com.br/search?q={quote_plus(q)}",
    "reddit": lambda q: f"https://www.reddit.com/search/?q={quote_plus(q)}",
    "reclame_aqui": lambda q: f"https://www.reclameaqui.com.br/busca/?q={quote_plus(q)}",
    "mercado_livre": _ml,
    "youtube_comments": lambda q: f"https://www.youtube.com/results?search_query={quote_plus(q)}",
    "google_trends": lambda q: f"https://trends.google.com.br/trends/explore?geo=BR&q={quote_plus(q)}",
    "meta_ads": lambda q: _meta_url(q),
}


def links_busca(fonte: str, queries: Iterable[str], limite: int = 3) -> list[dict]:
    """Retorna [{"query", "url"}] para abrir a busca da fonte à mão."""
    builder = _BUILDERS.get(fonte)
    if builder is None:
        return []
    out = []
    for q in list(queries)[:limite]:
        q = str(q).strip()
        if q:
            out.append({"query": q, "url": builder(q)})
    return out
