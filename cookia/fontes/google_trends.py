"""Google Trends BR — volume relativo + tendência (subindo/caindo).

Resolve a dor de 'números chutados' nos dossiês:
agora o Score 0-100 do Validator tem base real de volume e tendência.

Não usa pytrends pra evitar dependência pesada — bate direto no endpoint
público do Trends (interno, mas estável há anos).

Uso:
    from cookia.fontes.google_trends import volume_e_tendencia
    out = volume_e_tendencia(["chatbot empresarial", "agente IA"])
    # → [{"termo": ..., "volume_relativo": 78, "tendencia": "subindo", ...}]
"""
from __future__ import annotations
import time
from typing import Iterable

import httpx

EXPLORE = "https://trends.google.com/trends/api/explore"
MULTILINE = "https://trends.google.com/trends/api/widgetdata/multiline"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CookiaBot/1.0)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://trends.google.com/",
}


def _parse_jsonp(raw: str) -> dict | None:
    """Trends responde com prefixo ')]}',\\n' antes do JSON. Limpa e parseia."""
    import json
    if raw.startswith(")]}',"):
        raw = raw[5:]
    elif raw.startswith(")]}'"):
        raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return None


def _explore(termo: str, geo: str = "BR", timeframe: str = "today 12-m") -> dict | None:
    """Pega o token + widgets do termo. Necessário antes de chamar multiline."""
    import json as _json
    req = {
        "comparisonItem": [{"keyword": termo, "geo": geo, "time": timeframe}],
        "category": 0,
        "property": "",
    }
    params = {
        "hl": "pt-BR",
        "tz": "180",
        "req": _json.dumps(req, ensure_ascii=False),
    }
    try:
        with httpx.Client(timeout=10.0, headers=HEADERS) as c:
            r = c.get(EXPLORE, params=params)
        if r.status_code != 200:
            return None
        return _parse_jsonp(r.text)
    except httpx.HTTPError:
        return None


def _serie_temporal(token: str, req_widget: dict) -> list[int] | None:
    import json as _json
    params = {
        "hl": "pt-BR",
        "tz": "180",
        "req": _json.dumps(req_widget, ensure_ascii=False),
        "token": token,
    }
    try:
        with httpx.Client(timeout=10.0, headers=HEADERS) as c:
            r = c.get(MULTILINE, params=params)
        if r.status_code != 200:
            return None
        data = _parse_jsonp(r.text)
        if not data:
            return None
        timeline = data.get("default", {}).get("timelineData", [])
        return [int(p.get("value", [0])[0]) for p in timeline]
    except (httpx.HTTPError, KeyError, ValueError):
        return None


def _analisa_serie(serie: list[int]) -> dict:
    """Retorna volume médio e direção da tendência baseada na 2a metade vs 1a."""
    if not serie or len(serie) < 4:
        return {"volume_relativo": 0, "tendencia": "indefinida", "pico": 0}
    metade = len(serie) // 2
    media_inicio = sum(serie[:metade]) / max(metade, 1)
    media_fim = sum(serie[metade:]) / max(len(serie) - metade, 1)
    if media_inicio == 0:
        tend = "subindo" if media_fim > 0 else "indefinida"
    else:
        delta = (media_fim - media_inicio) / media_inicio
        if delta > 0.15:
            tend = "subindo"
        elif delta < -0.15:
            tend = "caindo"
        else:
            tend = "estavel"
    return {
        "volume_relativo": int(sum(serie) / len(serie)),
        "tendencia": tend,
        "pico": max(serie),
        "delta_pct": round((media_fim - media_inicio) / max(media_inicio, 1) * 100, 1) if media_inicio else 0,
    }


def volume_e_tendencia(termos: Iterable[str], *, geo: str = "BR", delay: float = 1.5) -> list[dict]:
    """Pra cada termo: volume_relativo (0-100), tendência, pico.

    Args:
        termos: lista de keywords a checar
        geo: geo do Google Trends (default BR)
        delay: pausa entre requests (Trends é sensível a rate-limit)

    Returns:
        list[{"termo", "volume_relativo", "tendencia", "pico", "delta_pct"}]
    """
    out = []
    for termo in termos:
        print(f"  📈 trends: {termo}")
        explore = _explore(termo, geo=geo)
        if not explore:
            out.append({"termo": termo, "volume_relativo": 0, "tendencia": "indisponivel"})
            time.sleep(delay)
            continue

        widgets = explore.get("widgets", [])
        timeseries_widget = next((w for w in widgets if w.get("id") == "TIMESERIES"), None)
        if not timeseries_widget:
            out.append({"termo": termo, "volume_relativo": 0, "tendencia": "indisponivel"})
            time.sleep(delay)
            continue

        token = timeseries_widget.get("token")
        req = timeseries_widget.get("request")
        if not (token and req):
            out.append({"termo": termo, "volume_relativo": 0, "tendencia": "indisponivel"})
            time.sleep(delay)
            continue

        serie = _serie_temporal(token, req)
        analise = _analisa_serie(serie or [])
        analise["termo"] = termo
        out.append(analise)
        time.sleep(delay)

    return out


if __name__ == "__main__":
    import json, sys
    termos = sys.argv[1:] or ["chatbot empresarial", "agente IA"]
    print(json.dumps(volume_e_tendencia(termos), ensure_ascii=False, indent=2))
