"""🪶 Agente Landing — preenche a estrutura de 9 seções com copy específica.

Pega persona escolhida + oferta principal do dossiê e gera a copy de cada seção
usando vocabulário REAL do público. Output: texto pronto pra colar no Lovable/Webflow/qualquer construtor.
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

from cookia.templates.landing_struct import LANDING_TEMPLATE, PROMPT_PREENCHER_LANDING, montar_landing_md


def landing(
    dossie: dict,
    persona_id: str | None = None,
    oferta_id: int | None = None,
    credenciais: str = "",
    *,
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Gera landing de 9 seções preenchida. Retorna {markdown, dados, persona_usada, oferta_usada}."""
    analyst = dossie.get("analyst", {})
    personas = analyst.get("personas", []) or []
    dores = analyst.get("dores", []) or []
    vocab = analyst.get("vocabulario_real", []) or []
    ofertas = dossie.get("validator", {}).get("ofertas", []) or dossie.get("strategist", {}).get("ofertas", [])

    # Resolve persona
    persona = None
    if persona_id:
        persona = next((p for p in personas if p.get("id") == persona_id), None)
    if not persona:
        persona = dossie.get("brief", {}).get("persona_escolhida")
    if not persona and personas:
        persona = personas[0]
    if not persona:
        return {"markdown": "_(nenhuma persona detectada — landing não gerada)_", "dados": {}, "persona_usada": None, "oferta_usada": None}

    # Resolve oferta
    if oferta_id:
        oferta = next((o for o in ofertas if o.get("id") == oferta_id), None)
    else:
        oferta = max(ofertas, key=lambda o: o.get("score", 0)) if ofertas else None
    if not oferta:
        return {"markdown": "_(nenhuma oferta gerada — landing não gerada)_", "dados": {}, "persona_usada": persona, "oferta_usada": None}

    # Dor central da persona
    ranks_persona = persona.get("dores_relacionadas_ranks", [])
    dores_p = [d for d in dores if d.get("rank") in ranks_persona] or [d for d in dores if d.get("persona_id") == persona.get("id")]
    dor_central = dores_p[0] if dores_p else (dores[0] if dores else {})

    vocab_block = "\n".join(f"- {t}" for t in vocab[:15])

    prompt = PROMPT_PREENCHER_LANDING.format(
        persona_nome=persona.get("nome", "?"),
        persona_desc=persona.get("descricao_uma_linha", "?"),
        persona_contexto=persona.get("contexto", "?"),
        persona_ticket=persona.get("ticket_alvo_estimado", "?"),
        persona_vocab=", ".join(persona.get("vocabulario_proprio", [])[:10]),
        dor_central=dor_central.get("dor", "?"),
        dor_frase=dor_central.get("frase_real_publico", "?"),
        dor_pain=dor_central.get("pain_score", "?"),
        oferta_nome=oferta.get("nome", "?"),
        oferta_promessa=oferta.get("promessa_numerica", "?"),
        oferta_ticket=oferta.get("ticket_sugerido", "?"),
        hook_principal=oferta.get("hook_de_venda", "?"),
        oferta_diferencial=oferta.get("diferencial", "?"),
        oferta_formato=oferta.get("formato", "?"),
        vocab_block=vocab_block,
    )

    print(f"\n🪶 [Landing] Persona: {persona.get('nome','?')} | Oferta: {oferta.get('nome','?')}")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(model=model, max_tokens=6000, messages=[{"role": "user", "content": prompt}])
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
    dados = json.loads(raw)
    dados["oferta_nome"] = oferta.get("nome", "?")

    md = montar_landing_md(LANDING_TEMPLATE, dados, credenciais=credenciais)
    print(f"    ✓ 9 seções preenchidas ({len(md)} chars)")
    return {
        "markdown": md,
        "dados": dados,
        "persona_usada": {"id": persona.get("id"), "nome": persona.get("nome")},
        "oferta_usada": {"id": oferta.get("id"), "nome": oferta.get("nome")},
    }
