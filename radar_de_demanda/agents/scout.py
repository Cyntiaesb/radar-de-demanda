"""🕵️ Agente Scout — coleta sinais de até 6 fontes (controlado pelo Router).

Aceita `routing_config` do Router pra:
  - Ativar/desativar fontes (ex: pular Mercado Livre pra serviço B2B)
  - Usar subreddits específicos por categoria
  - Buscar com queries comerciais reescritas

Reddit, Reclame Aqui, Mercado Livre e Google Trends bloqueiam coleta direta.
Com APIFY_TOKEN no `.env`, essas quatro vêm por coletores do Apify (com teto
de gasto, ver fontes/apify_fontes.py). Sem token, o Radar tenta direto e, se
a fonte falha ou volta vazia, registra "indisponível hoje" em `fontes_status`
com links de busca para a pessoa abrir à mão.
"""
from __future__ import annotations
from typing import Callable, Iterable

from ..fontes.google_autocomplete import scrape_google_signals
from ..fontes.reddit_br import scrape_reddit
from ..fontes.reclame_aqui import scrape_reclame_aqui
from ..fontes.google_trends import volume_e_tendencia
from ..fontes.mercado_livre import buscar_produtos, estatisticas_categoria
from ..fontes.youtube_comments import scrape_youtube_comments
from ..fontes.links_manuais import NOMES, links_busca
from ..fontes import apify_fontes as apify


def _registra(status: dict, fonte: str, n: int, queries: list[str], erro: str | None = None,
              via: str = "direto") -> None:
    ok = n > 0
    status[fonte] = {
        "nome": NOMES.get(fonte, fonte),
        "ok": ok,
        "n": n,
        "erro": erro,
        "via": via,
        "custo_usd": apify.GASTOS.get(fonte) if via == "apify" else None,
        "links": [] if ok else links_busca(fonte, queries),
    }
    if ok:
        extra = f" (Apify, US$ {status[fonte]['custo_usd']})" if via == "apify" else ""
        print(f"    ✓ {n} sinais{extra}")
    else:
        motivo = f" ({erro})" if erro else ""
        print(f"    ⚠ fonte indisponível hoje{motivo} — o dossiê traz links para abrir à mão")


def _coleta(status: dict, fonte: str, queries: list[str], fn: Callable[[], list],
            via: str = "direto") -> list:
    try:
        r = fn() or []
        _registra(status, fonte, len(r), queries, via=via)
        return r
    except Exception as e:  # falha numa fonte não derruba o pipeline
        _registra(status, fonte, 0, queries, erro=f"{type(e).__name__}: {e}"[:160], via=via)
        return []


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

    Returns:
        {"signals": [...], "trends": {...}, "market": {...},
         "fontes_status": {fonte: {"nome", "ok", "n", "erro", "links"}}}
    """
    cfg = routing_config or {}
    fontes_ativas = cfg.get("fontes_ativas", {})
    subreddits_cfg = cfg.get("subreddits_recomendados") or None
    queries_comerciais = cfg.get("queries_comerciais") or list(seeds)

    seeds_list = list(seeds)
    todas_queries = list(dict.fromkeys((queries_comerciais or []) + seeds_list))
    signals: list[dict] = []
    status: dict = {}
    usa_apify = apify.token() is not None
    apify.GASTOS.clear()
    if usa_apify:
        print(f"\n🕵️  Token do Apify encontrado: Reddit, Reclame Aqui, Mercado Livre e Trends vêm pelo Apify "
              f"(teto da rodada: US$ {apify.teto_rodada():.2f})")

    if fontes_ativas.get("google_autocomplete", True):
        print("\n🕵️  [Scout/1] Google Autocomplete BR...")
        g = _coleta(status, "google_autocomplete", todas_queries,
                    lambda: scrape_google_signals(todas_queries[:20], depth=1, delay=0.25))
        signals.extend(g[:max_google])

    if fontes_ativas.get("reddit", True):
        print("\n🕵️  [Scout/2] Reddit BR...")
        if usa_apify:
            r = _coleta(status, "reddit", todas_queries, lambda: apify.reddit(todas_queries), via="apify")
        else:
            kwargs = {"posts_per_query": 10, "comments_per_post": 2, "delay": 1.0}
            if subreddits_cfg:
                kwargs["subreddits"] = subreddits_cfg
            r = _coleta(status, "reddit", todas_queries, lambda: scrape_reddit(todas_queries[:10], **kwargs))
        signals.extend(r[:max_reddit])

    if fontes_ativas.get("reclame_aqui", True):
        print("\n🕵️  [Scout/3] Reclame Aqui BR...")
        if usa_apify:
            ra = _coleta(status, "reclame_aqui", todas_queries, lambda: apify.reclame_aqui(todas_queries),
                         via="apify")
        else:
            ra = _coleta(status, "reclame_aqui", todas_queries,
                         lambda: scrape_reclame_aqui(todas_queries[:8], max_per_query=15, delay=1.2))
        signals.extend(ra[:max_ra])

    market_stats: dict = {}
    if fontes_ativas.get("mercado_livre", True):
        print("\n🕵️  [Scout/4] Mercado Livre BR (demanda efetiva)...")
        if usa_apify:
            ml = _coleta(status, "mercado_livre", todas_queries, lambda: apify.mercado_livre(todas_queries),
                         via="apify")
        else:
            ml = _coleta(status, "mercado_livre", todas_queries,
                         lambda: buscar_produtos(todas_queries[:6], limit=20, delay=0.4))
        signals.extend(ml[:max_ml])
        if ml and usa_apify:
            market_stats = apify.estatisticas_ml(ml)
            print(f"    ✓ saturação: {market_stats.get('saturacao')}, preço médio: R${market_stats.get('preco_medio')}")
        elif ml:
            try:
                market_stats = estatisticas_categoria(todas_queries[:3])
                print(f"    ✓ saturação: {market_stats.get('saturacao')}, preço médio: R${market_stats.get('preco_medio')}")
            except Exception as e:
                print(f"    ⚠ estatísticas do Mercado Livre indisponíveis hoje: {e}")
    else:
        print("\n🕵️  [Scout/4] Mercado Livre BR — PULADO (Router: tipo de negócio não usa marketplace)")

    if fontes_ativas.get("youtube_comments", True) and (youtube_videos or fontes_ativas.get("youtube_search", False)):
        print("\n🕵️  [Scout/6] YouTube Comments...")
        yt = _coleta(status, "youtube_comments", todas_queries, lambda: scrape_youtube_comments(
            todas_queries[:5] if fontes_ativas.get("youtube_search", False) else (),
            videos=youtube_videos,
            max_videos_per_query=3,
            max_comments_per_video=50,
        ))
        signals.extend(yt[:max_yt])

    trends_map: dict = {}
    if fontes_ativas.get("google_trends", True):
        print("\n🕵️  [Scout/5] Google Trends BR (volume + tendência)...")
        try:
            tr = apify.google_trends(seeds_list) if usa_apify else volume_e_tendencia(seeds_list[:6], delay=1.5)
        except Exception as e:
            tr = []
            erro = f"{type(e).__name__}: {e}"[:160]
        else:
            erro = None
        validos = [t for t in tr if t.get("tendencia") not in (None, "indisponivel")]
        trends_map = {t["termo"]: t for t in validos}
        _registra(status, "google_trends", len(validos), seeds_list, erro=erro,
                  via="apify" if usa_apify else "direto")

    ok = [v["nome"] for v in status.values() if v["ok"]]
    print(f"\n🕵️  Scout terminou: {len(signals)} sinais; fontes com dado hoje: {', '.join(ok) or 'nenhuma'}")
    gasto = apify.resumo_gastos() if usa_apify else None
    if gasto:
        print(f"    💵 Apify nesta rodada: US$ {gasto['total_usd']:.4f} (teto US$ {gasto['teto_usd']:.2f})")
    return {
        "signals": signals,
        "trends": trends_map,
        "market": market_stats,
        "fontes_status": status,
        "apify": gasto,
    }
