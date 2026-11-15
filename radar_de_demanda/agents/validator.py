"""⚖️ Agente Validator — Market Viability Score 0-100 por oferta.

Score determinístico (não chuta, calcula):
  - Volume        (35%) — Pain Score da dor + trend de busca
  - Ticket        (25%) — ticket_sugerido vs ticket_medio do mercado
  - Saturação     (20%) — quanto mais saturado, menos score
  - Tendência     (20%) — subindo +20, caindo -20, estável 0

Output: cada oferta ganha um score 0-100 + veredito Go/No-Go.
"""
from __future__ import annotations


def _score_volume(pain_score: int, trend_volume: int) -> float:
    """Pain Score (0-100) pondera 70%, volume relativo Trends pondera 30%."""
    return 0.7 * pain_score + 0.3 * min(trend_volume, 100)


def _score_ticket(ticket_sugerido: str | None, ticket_medio: float | None) -> float:
    """Ticket próximo da média = 100. Muito acima (>3x) ou muito abaixo (<0.3x) penaliza.
    Sem dado de mercado = score neutro alto (não punir por falta de info)."""
    if not ticket_sugerido or not ticket_medio:
        return 70.0
    nums = [float(x.replace("R$", "").replace(".", "").replace(",", ".").strip())
            for x in ticket_sugerido.replace("/", " ").split() if any(c.isdigit() for c in x)]
    if not nums:
        return 50.0
    ticket = nums[0]
    if ticket_medio == 0:
        return 50.0
    ratio = ticket / ticket_medio
    if 0.5 <= ratio <= 2.0:
        return 100.0
    elif 0.3 <= ratio < 0.5 or 2.0 < ratio <= 3.0:
        return 70.0
    elif 0.15 <= ratio < 0.3 or 3.0 < ratio <= 5.0:
        return 40.0
    else:
        return 20.0


def _score_saturacao(saturacao: str) -> float:
    """Saturação baixa = oportunidade (100), alta = vermelho (30).
    Indefinida = neutro otimista (70) — não punir por falta de dado."""
    return {"baixa": 100.0, "media": 65.0, "alta": 30.0, "indefinida": 70.0}.get(saturacao, 70.0)


def _score_tendencia(tendencia: str, delta_pct: float = 0) -> float:
    base = {"subindo": 85, "estavel": 60, "caindo": 25, "indefinida": 50}.get(tendencia, 50)
    if tendencia == "subindo" and delta_pct > 40:
        base = min(100, base + 15)
    return float(base)


def _veredito(score: float) -> tuple[str, str]:
    if score >= 65:
        return "🟢", "Go — atacar nos próximos 30 dias"
    elif score >= 50:
        return "🟡", "Espera — refine ângulo ou valide com piloto"
    else:
        return "🔴", "No-Go — não atacar agora"


def validator(
    strategist_out: dict,
    analyst_out: dict,
    hunter_out: dict,
    trends: dict,
) -> dict:
    """Adiciona Market Viability Score 0-100 a cada oferta do Strategist.

    Retorna o mesmo dict do Strategist com 'score' e 'veredito' em cada oferta.
    """
    print("\n⚖️  [Validator] Calculando Market Viability Score 0-100...")

    dores = {d.get("rank"): d for d in analyst_out.get("dores", [])}
    ticket_medio = hunter_out.get("fórmula_vencedora", {}).get("ticket_medio_top_10") or 0
    saturacao = hunter_out.get("fórmula_vencedora", {}).get("saturacao", "indefinida")

    trend_volumes = [t.get("volume_relativo", 0) for t in trends.values()]
    trend_volume_avg = sum(trend_volumes) / len(trend_volumes) if trend_volumes else 0

    tendencias = [t.get("tendencia") for t in trends.values()]
    if not tendencias:  # Trends indisponível hoje: sem dado, sem bônus de tendência
        tendencia_dom = "indefinida"
    elif tendencias.count("subindo") >= len(tendencias) / 2:
        tendencia_dom = "subindo"
    elif tendencias.count("caindo") >= len(tendencias) / 2:
        tendencia_dom = "caindo"
    else:
        tendencia_dom = "estavel"

    deltas = [t.get("delta_pct", 0) for t in trends.values()]
    delta_avg = sum(deltas) / len(deltas) if deltas else 0

    ofertas_scored = []
    for of in strategist_out.get("ofertas", []):
        dor_str = str(of.get("dor_atacada", ""))
        rank = next((int(c) for c in dor_str.split() if c.isdigit()), 1)
        dor = dores.get(rank, {})
        pain = dor.get("pain_score", 50)

        s_volume = _score_volume(pain, int(trend_volume_avg))
        s_ticket = _score_ticket(of.get("ticket_sugerido"), ticket_medio if isinstance(ticket_medio, (int, float)) else 0)
        s_saturacao = _score_saturacao(saturacao)
        s_tendencia = _score_tendencia(tendencia_dom, delta_avg)

        # Pesos: Pain Score é o sinal mais confiável (Sonnet analisou contexto),
        # então peso maior. Mercado/Trends são complementares.
        score_final = round(
            0.45 * s_volume +
            0.20 * s_ticket +
            0.15 * s_saturacao +
            0.20 * s_tendencia
        )
        emoji, veredito_txt = _veredito(score_final)

        of["score"] = score_final
        of["score_breakdown"] = {
            "volume": round(s_volume),
            "ticket": round(s_ticket),
            "saturacao": round(s_saturacao),
            "tendencia": round(s_tendencia),
        }
        of["veredito"] = veredito_txt
        of["semaforo"] = emoji
        ofertas_scored.append(of)

    ofertas_scored.sort(key=lambda o: o.get("score", 0), reverse=True)

    go = sum(1 for o in ofertas_scored if o.get("score", 0) >= 75)
    print(f"    ✓ {len(ofertas_scored)} ofertas validadas — {go} 🟢 Go, "
          f"{sum(1 for o in ofertas_scored if 55 <= o.get('score',0) < 75)} 🟡, "
          f"{sum(1 for o in ofertas_scored if o.get('score',0) < 55)} 🔴")

    return {"ofertas": ofertas_scored}
