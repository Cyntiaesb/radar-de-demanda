"""Fontes de sinal pro Demand Intelligence.

Cada fonte expõe função `scrape_*` que retorna lista de dicts:
    [{"texto": str, "fonte": str, "url": str, "metadata": dict}]
"""
from .reddit_br import scrape_reddit

__all__ = ["scrape_reddit"]
