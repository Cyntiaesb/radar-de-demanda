"""Scraper Google Autocomplete + Related Searches.

Estratégia MVP: usar Google Autocomplete (endpoint público sem auth).
Pra cada seed, expande com modificadores (como, quanto, quando, etc + a-z).

Output: lista de tuplas (sinal, seed_origem, fonte).

Próximas iterações: adicionar PAA (People Also Ask) via Apify ou Playwright.
"""
from __future__ import annotations
import time
import urllib.parse
from typing import Iterable

import requests

_AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

# Modificadores que geram perguntas reais
_MODIFICADORES_PERGUNTA = ["como", "quanto", "quando", "qual", "onde", "por que", "preciso de"]
_LETRAS = "abcdefghijklmnopqrstuvwxyz"


def _autocomplete(query: str, hl: str = "pt-BR", gl: str = "br") -> list[str]:
    """Chama endpoint público de autocomplete do Google. Retorna lista de sugestões."""
    try:
        r = requests.get(
            _AUTOCOMPLETE_URL,
            params={
                "client": "chrome",
                "hl": hl,
                "gl": gl,
                "q": query,
            },
            headers=_HEADERS,
            timeout=8,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        # Formato: [query, [sug1, sug2, ...], ...]
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            return [str(s).strip() for s in data[1] if s]
    except Exception:
        return []
    return []


def scrape_seed(seed: str, *, depth: int = 1, delay: float = 0.25) -> list[tuple[str, str]]:
    """Pra 1 seed, retorna [(sinal, fonte), ...].

    depth=1: só modificadores de pergunta (rápido, ~7 queries × 10 sugestões = ~70 sinais)
    depth=2: + expansão a-z (~33 queries × 10 = ~330 sinais)
    """
    visto: set[str] = set()
    sinais: list[tuple[str, str]] = []

    queries = [seed]
    for mod in _MODIFICADORES_PERGUNTA:
        queries.append(f"{mod} {seed}")
    if depth >= 2:
        for c in _LETRAS:
            queries.append(f"{seed} {c}")

    for q in queries:
        sugs = _autocomplete(q)
        for s in sugs:
            s_clean = s.strip().lower()
            if s_clean and s_clean != q.lower() and s_clean not in visto:
                visto.add(s_clean)
                sinais.append((s, f"autocomplete:{q}"))
        time.sleep(delay)

    return sinais


def scrape_google_signals(seeds: Iterable[str], *, depth: int = 1, delay: float = 0.25) -> list[dict]:
    """Pra uma lista de seeds, retorna lista de sinais únicos.

    Cada sinal: {"sinal": str, "seed": str, "fonte": str}
    """
    out: list[dict] = []
    visto_global: set[str] = set()
    for seed in seeds:
        print(f"  🔍 {seed}")
        for sinal, fonte in scrape_seed(seed, depth=depth, delay=delay):
            key = sinal.lower().strip()
            if key in visto_global:
                continue
            visto_global.add(key)
            out.append({"sinal": sinal, "seed": seed, "fonte": fonte})
    return out
