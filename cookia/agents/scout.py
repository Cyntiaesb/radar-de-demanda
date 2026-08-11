"""🕵️ Agente Scout — coleta sinais de até 5 fontes (controlado pelo Router).

Aceita `routing_config` do Router pra:
  - Ativar/desativar fontes (ex: pular Mercado Livre pra serviço B2B)
  - Usar subreddits específicos por categoria
  - Buscar com queries comerciais reescritas
"""
from __future__ import annotations
from typing import Iterable

from ..fontes.google_autocomplete import scrape_google_signals
from ..fontes.reddit_br import scrape_reddit
from ..fontes.reclame_aqui import scrape_reclame_aqui
from ..fontes.google_trends import volume_e_tendencia
from ..fontes.mercado_livre import buscar_produtos, estatisticas_categoria
from ..fontes.youtube_comments import scrape_youtube_comments


def scout(
    seeds: Iterable[str],
    *,
    routing_config: dict | None = None,
    max_google: int = 300,
    max_reddit: int = 200,
    max_ra: int = 100,
    max_ml: int = 60,
    max_yt: int = 100,
    youtube_videos: list[str] | None = None,
) -> dict:
    """Roda as fontes ativadas pelo Router. Falha numa fonte não derruba pipeline.

    Args:
        seeds: queries seed (já podem vir reescritas pelo Router)
        routing_config: opcional, do Router. Se None, ativa tudo.
    """
    cfg = routing_config or {}
    fontes_ativas = cfg.get("fontes_ativas", {})
    subreddits_cfg = cfg.get("subreddits_recomendados") or None
    queries_comerciais = cfg.get("queries_comerciais") or list(seeds)

    seeds_list = list(seeds)
    todas_queries = list(dict.fromkeys((queries_comerciais or []) + seeds_list))
    signals: list[dict] = []

    if fontes_ativas.get("google_autocomplete", True):
        print("\n🕵️  [Scout/1] Google Autocomplete BR...")
        try:
            g = scrape_google_signals(todas_queries[:20], depth=1, delay=0.25)
            signals.extend(g[:max_google])
            print(f"    ✓ {len(g)} sinais")
        except Exception as e:
            print(f"    ⚠ falhou: {e}")

    if fontes_ativas.get("reddit", True):
        print("\n🕵️  [Scout/2] Reddit BR...")
        try:
            kwargs = {"posts_per_query": 10, "comments_per_post": 2, "delay": 1.0}
            if subreddits_cfg:
                kwargs["subreddits"] = subreddits_cfg
            r = scrape_reddit(todas_queries[:10], **kwargs)
            signals.extend(r[:max_reddit])
            print(f"    ✓ {len(r)} sinais (subs: {len(subreddits_cfg) if subreddits_cfg else 'default'})")
        except Exception as e:
            print(f"    ⚠ falhou: {e}")

    if fontes_ativas.get("reclame_aqui", True):
        print("\n🕵️  [Scout/3] Reclame Aqui BR...")
        try:
            ra = scrape_reclame_aqui(todas_queries[:8], max_per_query=15, delay=1.2)
            signals.extend(ra[:max_ra])
            print(f"    ✓ {len(ra)} reclamações")
        except Exception as e:
            print(f"    ⚠ falhou: {e}")

    market_stats = {}
    if fontes_ativas.get("mercado_livre", True):
        print("\n🕵️  [Scout/4] Mercado Livre BR (demanda efetiva)...")
        try:
            ml = buscar_produtos(todas_queries[:6], limit=20, delay=0.4)
            signals.extend(ml[:max_ml])
            print(f"    ✓ {len(ml)} produtos")
            market_stats = estatisticas_categoria(todas_queries[:3])
            print(f"    ✓ saturação: {market_stats.get('saturacao')}, preço médio: R${market_stats.get('preco_medio')}")
        except Exception as e:
            print(f"    ⚠ falhou: {e}")
    else:
        print("\n🕵️  [Scout/4] Mercado Livre BR — PULADO (Router: tipo de negócio não usa marketplace)")

    if fontes_ativas.get("youtube_comments", True) and (youtube_videos or fontes_ativas.get("youtube_search", False)):
        print("\n🕵️  [Scout/6] YouTube Comments...")
        try:
            yt = scrape_youtube_comments(
                todas_queries[:5] if fontes_ativas.get("youtube_search", False) else (),
                videos=youtube_videos,
                max_videos_per_query=3,
                max_comments_per_video=50,
            )
            signals.extend(yt[:max_yt])
            print(f"    ✓ {len(yt)} comentários")
        except Exception as e:
            print(f"    ⚠ falhou: {e}")

    trends_map: dict = {}
    if fontes_ativas.get("google_trends", True):
        print("\n🕵️  [Scout/5] Google Trends BR (volume + tendência)...")
        try:
            tr = volume_e_tendencia(seeds_list[:6], delay=1.5)
            trends_map = {t["termo"]: t for t in tr}
            subindo = sum(1 for t in tr if t.get("tendencia") == "subindo")
            print(f"    ✓ {len(tr)} termos ({subindo} subindo)")
        except Exception as e:
            print(f"    ⚠ falhou: {e}")

    print(f"\n🕵️  Scout terminou: {len(signals)} sinais de {sum(1 for v in fontes_ativas.values() if v)} fontes ativas")
    return {
        "signals": signals,
        "trends": trends_map,
        "market": market_stats,
    }
