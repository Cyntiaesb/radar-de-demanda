"""Fontes pelo Apify: Reddit, Reclame Aqui, Mercado Livre e Google Trends.

Esses sites bloqueiam coleta direta (anti-robô, login, limite de pedidos).
Com um token do Apify no `.env` (APIFY_TOKEN=...), o Radar usa coletores
prontos do Apify, que passam por esses bloqueios. Sem token, nada aqui roda
e o dossiê entrega os links para abrir à mão.

Custo: cada coletor roda com teto de gasto (`maxTotalChargeUsd`). O teto da
rodada inteira vem de APIFY_TETO_USD no `.env` (padrão US$ 1,00) e é dividido
entre as fontes. O custo real de cada coletor é lido do Apify no fim e vai
para o dossiê.
"""
from __future__ import annotations

import os
import time
from typing import Callable, Iterable

import requests

API = "https://api.apify.com/v2"

# Coletor de cada fonte e a fatia do teto da rodada que ele pode gastar.
ATORES = {
    "reddit": ("practicaltools/apify-reddit-api", 0.15),
    "reclame_aqui": ("blackfalcondata/reclameaqui-scraper", 0.40),
    "mercado_livre": ("karamelo/mercadolivre-scraper-brasil-portugues", 0.15),
    "google_trends": ("apify/google-trends-scraper", 0.10),
    "meta_ads": ("jmlp/meta-ad-library-scraper", 0.20),
}

# Gasto real de cada coletor nesta rodada: {fonte: usd}
GASTOS: dict[str, float] = {}


def token() -> str | None:
    t = (os.environ.get("APIFY_TOKEN") or "").strip()
    return t or None


def teto_rodada() -> float:
    try:
        return max(0.0, float(os.environ.get("APIFY_TETO_USD", "1.0").replace(",", ".")))
    except ValueError:
        return 1.0


def teto_da_fonte(fonte: str) -> float:
    return round(teto_rodada() * ATORES[fonte][1], 2)


def _roda(fonte: str, entrada: dict, *, espera: int = 300, http=requests) -> list[dict]:
    """Roda o coletor da fonte com teto de gasto e devolve os itens."""
    tk = token()
    if not tk:
        raise RuntimeError("sem APIFY_TOKEN no .env")
    ator, _ = ATORES[fonte]
    teto = teto_da_fonte(fonte)
    if teto <= 0:
        raise RuntimeError("teto do Apify é zero (APIFY_TETO_USD)")
    cab = {"Authorization": f"Bearer {tk}"}
    params = {"maxTotalChargeUsd": teto, "timeout": espera, "waitForFinish": 60}
    r = http.post(f"{API}/acts/{ator.replace('/', '~')}/runs", params=params, json=entrada,
                  headers=cab, timeout=90)
    if r.status_code == 401:
        raise RuntimeError("o Apify recusou o token (confira o APIFY_TOKEN no .env)")
    r.raise_for_status()
    run = r.json()["data"]
    limite = time.time() + espera + 60
    while run.get("status") in ("READY", "RUNNING") and time.time() < limite:
        time.sleep(5)
        r = http.get(f"{API}/actor-runs/{run['id']}", headers=cab, timeout=30)
        r.raise_for_status()
        run = r.json()["data"]
    GASTOS[fonte] = round(float(run.get("usageTotalUsd") or 0), 4)
    if run.get("status") not in ("SUCCEEDED", "ABORTED", "TIMED-OUT"):
        raise RuntimeError(f"coletor do Apify terminou com status {run.get('status')}")
    r = http.get(f"{API}/datasets/{run['defaultDatasetId']}/items",
                 params={"clean": "true", "limit": 1000}, headers=cab, timeout=60)
    r.raise_for_status()
    itens = r.json()
    return itens if isinstance(itens, list) else []


def _primeiro(d: dict, *chaves, padrao=None):
    for c in chaves:
        v = d.get(c)
        if v not in (None, "", []):
            return v
    return padrao


def _numero(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("R$", "").replace("\xa0", "").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ---------- conversores: item do Apify -> sinal do Radar ----------

def sinal_reddit(it: dict) -> dict | None:
    titulo = _primeiro(it, "title", padrao="")
    corpo = _primeiro(it, "body", "text", "selftext", padrao="")
    texto = f"{titulo}. {corpo}".strip(". ").strip()
    if not texto:
        return None
    comunidade = _primeiro(it, "parsedCommunityName", "communityName", "subreddit", padrao="")
    comunidade = str(comunidade).replace("r/", "")
    eh_comentario = str(_primeiro(it, "dataType", padrao="post")) == "comment"
    return {
        "texto": texto[:2000],
        "fonte": f"reddit{'-comment' if eh_comentario else ''}:r/{comunidade}",
        "url": _primeiro(it, "url", "link", padrao=""),
        "metadata": {
            "score": _primeiro(it, "upVotes", "score", padrao=0),
            "num_comments": _primeiro(it, "numberOfComments", "num_comments", padrao=0),
            "subreddit": comunidade,
            "via": "apify",
        },
    }


def sinal_reclame_aqui(it: dict) -> dict | None:
    if str(it.get("recordType", "complaint")).lower() not in ("complaint", "reclamacao"):
        return None
    titulo = _primeiro(it, "title", padrao="")
    desc = _primeiro(it, "description", "descriptionText", "text", padrao="")
    texto = f"{titulo}. {desc}".strip(". ").strip()
    if not texto:
        return None
    return {
        "texto": texto[:2000],
        "fonte": "reclame_aqui",
        "url": _primeiro(it, "url", padrao=""),
        "metadata": {
            "empresa": _primeiro(it, "name", "companyName", "companySlug"),
            "status": _primeiro(it, "statusLabel", "status"),
            "data": _primeiro(it, "created"),
            "via": "apify",
        },
    }


def sinal_mercado_livre(it: dict, query: str = "") -> dict | None:
    titulo = str(_primeiro(it, "eTituloProduto", "title", "titulo", padrao="")).strip()
    if not titulo:
        return None
    return {
        "texto": titulo,
        "fonte": "mercado_livre",
        "url": _primeiro(it, "zProdutoLink", "url", "permalink", padrao=""),
        "metadata": {
            "query": _primeiro(it, "palavraChave", padrao=query),
            "preco": _numero(_primeiro(it, "novoPreco", "price", "preco")),
            "moeda": _primeiro(it, "Moeda", padrao="BRL"),
            "vendidos": _numero(_primeiro(it, "quantidadeVendida", "sold_quantity")),
            "avaliacoes": _numero(_primeiro(it, "numeroAvaliacoes")),
            "via": "apify",
        },
    }


def _analisa_serie(serie: list[float]) -> dict:
    from .google_trends import _analisa_serie as analisa
    return analisa([int(v) for v in serie])


def tendencia_trends(it: dict) -> dict | None:
    termo = _primeiro(it, "searchTerm", "inputUrlOrTerm", "term")
    linha = _primeiro(it, "interestOverTime_timelineData", "timelineData", padrao=[])
    serie = []
    for ponto in linha or []:
        v = ponto.get("value")
        if isinstance(v, list):
            v = v[0] if v else None
        if isinstance(v, (int, float)):
            serie.append(v)
    if not termo or len(serie) < 4:
        return None
    out = _analisa_serie(serie)
    out["termo"] = termo
    out["via"] = "apify"
    return out


def _converte(itens: Iterable[dict], fn: Callable[[dict], dict | None]) -> list[dict]:
    out, vistos = [], set()
    for it in itens:
        s = fn(it)
        if not s:
            continue
        chave = (s.get("url") or s.get("termo") or s.get("texto", ""))[:300]
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append(s)
    return out


# ---------- as quatro fontes ----------

def reddit(queries: list[str], *, max_itens: int = 60, http=requests) -> list[dict]:
    entrada = {
        "searches": queries[:6], "startUrls": [], "ignorestartUrls": True,
        "searchPosts": True, "searchComments": True, "fetchPostComments": False,
        "skipCommunity": True, "skipUserPosts": True, "includeNSFW": False,
        "sort": "relevance", "time": "year", "maxItems": max_itens,
    }
    return _converte(_roda("reddit", entrada, http=http), sinal_reddit)


def reclame_aqui(queries: list[str], *, max_itens: int = 40, http=requests) -> list[dict]:
    qs = queries[:4]
    entrada = {
        "companies": [], "searchQueries": qs,
        "includeCompanyProfile": False, "scrapeComplaints": True,
        "includeInteractions": False, "extractContacts": False,
        "maxComplaintsPerCompany": max(1, max_itens // max(len(qs), 1)),
        "maxItems": max_itens, "descriptionFormat": "text", "descriptionMaxLength": 1500,
    }
    return _converte(_roda("reclame_aqui", entrada, http=http), sinal_reclame_aqui)


def mercado_livre(queries: list[str], *, http=requests) -> list[dict]:
    # O coletor aceita uma palavra por rodada: usa a principal.
    q = queries[0] if queries else ""
    entrada = {"keyword": q, "maxPages": 1, "scrapeOfertas": False, "promoted": False}
    return _converte(_roda("mercado_livre", entrada, http=http), lambda it: sinal_mercado_livre(it, q))


def estatisticas_ml(sinais: list[dict]) -> dict:
    precos = [s["metadata"]["preco"] for s in sinais if s["metadata"].get("preco")]
    vendidos = [s["metadata"].get("vendidos") or 0 for s in sinais]
    if not sinais:
        return {"total": 0, "saturacao": "indefinida"}
    return {
        "total_anuncios_amostra": len(sinais),
        "preco_medio": round(sum(precos) / len(precos), 2) if precos else None,
        "preco_min": min(precos) if precos else None,
        "preco_max": max(precos) if precos else None,
        "total_vendidos_amostra": int(sum(vendidos)),
        "top_vendido": int(max(vendidos)) if vendidos else 0,
        "saturacao": "alta" if len(sinais) >= 25 else "media" if len(sinais) >= 10 else "baixa",
    }


def google_trends(termos: list[str], *, http=requests) -> list[dict]:
    entrada = {"searchTerms": termos[:5], "isMultiple": False, "geo": "BR",
               "timeRange": "today 12-m", "maxItems": len(termos[:5])}
    return _converte(_roda("google_trends", entrada, http=http), tendencia_trends)


def _data(ts):
    from datetime import date, datetime, timezone
    if ts in (None, ""):
        return None
    try:
        if isinstance(ts, (int, float)) or str(ts).isdigit():
            return datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
        return date.fromisoformat(str(ts)[:10])
    except (ValueError, OSError):
        return None


def anuncio_meta(it: dict, hoje=None) -> dict | None:
    from datetime import date
    s = it.get("snapshot") or {}
    b = s.get("body")
    texto = b.get("text") if isinstance(b, dict) else b
    if not texto or "{{" in str(texto):
        cards = s.get("cards") or []
        texto = (cards[0].get("body") if cards else "") or s.get("title") or ""
    texto = " ".join(str(texto).split())
    if not texto:
        return None
    hoje = hoje or date.today()
    ini, fim = _data(it.get("start_date")), _data(it.get("end_date"))
    ativo = bool(it.get("is_active"))
    dias = ((hoje if ativo else (fim or hoje)) - ini).days if ini else None
    return {
        "texto": texto[:1500],
        "pagina": it.get("page_name") or "?",
        "dias_rodando": dias,
        "ativo": ativo,
        "url": f"https://www.facebook.com/ads/library/?id={it['ad_archive_id']}" if it.get("ad_archive_id") else "",
        "link_destino": s.get("link_url") or "",
        "via": "apify",
    }


def meta_anuncios(keywords: list[str], *, max_anuncios: int = 40, http=requests) -> list[dict]:
    from .meta_ads_library import build_search_url
    entrada = {"adLibraryUrls": [build_search_url(k, country="BR") for k in keywords[:5]],
               "maxAds": max_anuncios}
    itens = _roda("meta_ads", entrada, http=http)
    out, vistos = [], set()
    for it in itens:
        a = anuncio_meta(it)
        if not a:
            continue
        chave = a["texto"][:100] + a["pagina"]
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append(a)
    return out


def resumo_gastos() -> dict:
    total = round(sum(GASTOS.values()), 4)
    return {"por_fonte": dict(GASTOS), "total_usd": total, "teto_usd": teto_rodada()}
