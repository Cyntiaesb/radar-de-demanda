"""Reddit BR — captura posts e comentários relevantes pro nicho.

Usa endpoint público old.reddit.com/search.json (sem auth, sem custo Apify).

Estratégia: pra cada query, busca em subreddits brasileiros relevantes + busca geral.
Pega title + selftext + top N comentários de cada post.
"""
from __future__ import annotations
import time
import requests

_HEADERS = {
    "User-Agent": "RadarDeDemandaBot/1.0 (research; contato via github.com/Cyntiaesb)",
    "Accept": "application/json",
}

# Termos políticos/governo BR que contaminam o dossiê — usado em filtro pós-coleta.
# Se um post contém >= 2 desses termos, é descartado.
POLITICAL_NOISE_TERMS = [
    "lula", "bolsonaro", "stf", "moraes", "alexandre de moraes",
    "pt ", "pl ", "psol", "psdb", "pdt", "republicanos", "novo",
    "eleição", "eleicao", "eleicoes", "eleições", "2026", "2022",
    "anistia", "presidente", "ministro", "ministra", "câmara", "senado",
    "deputado", "deputada", "vereador", "senador",
    "esquerda", "direita", "comunist", "fascis", "esquerdopat", "petralh",
    "datafolha", "ipec", "quaest", "atlasintel",
    "governo federal", "ministério", "ministerio",
    "supremo tribunal", "tribunal federal",
    "stf", "tse", "tcu", "agu", "pgr",
]


def _eh_politico(texto: str) -> bool:
    """Detecta se o texto é majoritariamente sobre política BR (contamina dossiê)."""
    t = texto.lower()
    hits = sum(1 for term in POLITICAL_NOISE_TERMS if term in t)
    return hits >= 2


# Subreddits brasileiros — focados em DOR PROFISSIONAL e NICHOS.
# r/brasil e r/brasilivre foram REMOVIDOS — viram noise (política/notícia) e contaminam o dossiê.
SUBREDDITS_BR = [
    "empreendedorismo",
    "investimentos",
    "PoupadosNet",
    "conselhodecarreira",
    "trabalhoecarreira",
    "desabafos",
    "AskBrasil",
    "DesignBR",
    "marketingdigital",
    "vendas",
    "freelaBR",
    "TIBrasil",
    "brdev",
    "contabilidade",
    "direito",
    "advocacia",
]


def _fetch(url: str, params: dict | None = None, retries: int = 2) -> dict | None:
    for i in range(retries):
        try:
            r = requests.get(url, params=params or {}, headers=_HEADERS, timeout=10)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(3)
                continue
        except Exception:
            time.sleep(1)
    return None


def _busca_subreddit(query: str, subreddit: str, limit: int = 25) -> list[dict]:
    """Busca posts num subreddit específico."""
    url = f"https://old.reddit.com/r/{subreddit}/search.json"
    data = _fetch(url, {
        "q": query,
        "restrict_sr": "on",
        "sort": "relevance",
        "t": "year",  # últimos 12 meses
        "limit": limit,
    })
    if not data:
        return []
    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        if not d.get("title"):
            continue
        posts.append({
            "texto": f"{d.get('title', '')}. {d.get('selftext', '')}".strip()[:2000],
            "fonte": f"reddit:r/{subreddit}",
            "url": f"https://reddit.com{d.get('permalink', '')}",
            "metadata": {
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "subreddit": subreddit,
                "post_id": d.get("id", ""),
            },
        })
    return posts


def _comentarios_top(post_id: str, subreddit: str, limit: int = 5) -> list[dict]:
    """Pega top N comentários de um post."""
    url = f"https://old.reddit.com/r/{subreddit}/comments/{post_id}.json"
    data = _fetch(url, {"limit": limit, "sort": "top"})
    if not data or not isinstance(data, list) or len(data) < 2:
        return []
    out = []
    for child in data[1].get("data", {}).get("children", [])[:limit]:
        d = child.get("data", {})
        body = d.get("body", "")
        if not body or body in ("[deleted]", "[removed]"):
            continue
        out.append({
            "texto": body[:1500],
            "fonte": f"reddit-comment:r/{subreddit}",
            "url": f"https://reddit.com{d.get('permalink', '')}",
            "metadata": {
                "score": d.get("score", 0),
                "subreddit": subreddit,
            },
        })
    return out


def scrape_reddit(queries: list[str], *, subreddits: list[str] | None = None,
                  posts_per_query: int = 15, comments_per_post: int = 3,
                  delay: float = 1.0) -> list[dict]:
    """Roda busca multi-query em subreddits BR. Retorna lista de sinais.

    Cada sinal: {"texto": str, "fonte": str, "url": str, "metadata": dict}
    """
    subreddits = subreddits or SUBREDDITS_BR
    out: list[dict] = []
    visto: set[str] = set()
    descartados_politicos = 0

    for q in queries:
        print(f"  🔍 reddit query: {q}")
        for sub in subreddits:
            posts = _busca_subreddit(q, sub, limit=posts_per_query)
            for p in posts:
                pid = p["metadata"]["post_id"]
                if pid in visto:
                    continue
                visto.add(pid)
                # Filtro político — descarta sinais contaminados com discurso político
                if _eh_politico(p.get("texto", "")):
                    descartados_politicos += 1
                    continue
                out.append(p)
                if comments_per_post > 0:
                    for c in _comentarios_top(pid, sub, limit=comments_per_post):
                        if _eh_politico(c.get("texto", "")):
                            descartados_politicos += 1
                            continue
                        out.append(c)
                time.sleep(delay * 0.5)
            time.sleep(delay)

    if descartados_politicos:
        print(f"    🚫 {descartados_politicos} sinais políticos descartados")
    return out
