"""Gera uma landing page de captura (9 seções) baseada no dossiê + persona escolhida.

Uso:
    python scripts/gerar_landing.py                 # usa último dossiê + persona escolhida nele
    python scripts/gerar_landing.py P2              # outra persona id do mesmo dossiê
    python scripts/gerar_landing.py P2 --oferta 3   # outra oferta principal
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from anthropic import Anthropic
from cookia.templates.landing_struct import LANDING_TEMPLATE, PROMPT_PREENCHER_LANDING, montar_landing_md

DOSSIES = ROOT / "data" / "dossies"


def _ultimo_dossie() -> Path:
    jsons = sorted(DOSSIES.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsons:
        print("❌ Nenhum dossiê. Rode `python scripts/cookia_run.py \"nicho\"` primeiro.")
        sys.exit(1)
    return jsons[0]


def gerar_landing(dossie: dict, persona_id: str | None, oferta_id: int | None, credenciais: str = "") -> tuple[str, dict]:
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
        print("❌ Nenhuma persona detectada no dossiê.")
        sys.exit(1)

    # Resolve oferta
    if oferta_id:
        oferta = next((o for o in ofertas if o.get("id") == oferta_id), None)
        if not oferta:
            print(f"❌ Oferta #{oferta_id} não encontrada.")
            sys.exit(1)
    else:
        oferta = max(ofertas, key=lambda o: o.get("score", 0)) if ofertas else {}

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
    print("   Gerando 14 blocos de copy...")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=6000, messages=[{"role": "user", "content": prompt}])
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
    dados = json.loads(raw)
    dados["oferta_nome"] = oferta.get("nome", "?")

    md = montar_landing_md(LANDING_TEMPLATE, dados, credenciais=credenciais)
    return md, dados


def main():
    p = argparse.ArgumentParser()
    p.add_argument("persona_id", nargs="?", default=None, help="ID da persona (ex: P1, P2). Default: a escolhida no dossiê.")
    p.add_argument("--oferta", type=int, default=None, help="ID da oferta principal (default: maior score)")
    p.add_argument("--credenciais", default="", help="Bloco de credenciais (texto livre — opcional)")
    p.add_argument("--dossie", default=None, help="Path do JSON do dossiê (default: mais recente)")
    args = p.parse_args()

    json_path = Path(args.dossie) if args.dossie else _ultimo_dossie()
    print(f"📂 Dossiê: {json_path.name}")
    dossie = json.loads(json_path.read_text(encoding="utf-8"))

    md, dados = gerar_landing(dossie, args.persona_id, args.oferta, args.credenciais)

    out_path = json_path.with_name(json_path.stem + "_landing.md")
    out_path.write_text(md, encoding="utf-8")
    print(f"\n✅ Landing gerada: {out_path}")
    print(f"\n📋 Abra no Claude Code pra ver renderizada:")
    print(f"   code {out_path}")


if __name__ == "__main__":
    main()
