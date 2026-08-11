"""Demand Intelligence — captura sinais de demanda real do mercado."""
from .seeds import SEEDS
from .fontes.google_autocomplete import scrape_google_signals
from .fontes.reddit_br import scrape_reddit
from .fontes.reclame_aqui import scrape_reclame_aqui

__all__ = ["SEEDS", "scrape_google_signals", "scrape_reddit", "scrape_reclame_aqui"]
