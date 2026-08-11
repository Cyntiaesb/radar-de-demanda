"""Renderiza HTML do dossiê mais recente (sem rodar pipeline de novo).

Uso:
    python scripts/render_html_existente.py
    python scripts/render_html_existente.py data/dossies/<nome>.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cookia.render_html import render_html

DOSSIES = ROOT / "data" / "dossies"


def main():
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        jsons = sorted(DOSSIES.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not jsons:
            print("❌ Nenhum dossiê encontrado em data/dossies/")
            sys.exit(1)
        json_path = jsons[0]

    print(f"📂 Lendo: {json_path.name}")
    dossie = json.loads(json_path.read_text(encoding="utf-8"))

    html = render_html(
        nicho=dossie.get("nicho", "?"),
        brief=dossie.get("brief", {}),
        routing=dossie.get("routing", {}),
        analyst_out=dossie.get("analyst", {}),
        hunter_out=dossie.get("hunter", {}),
        info_hunter_out=dossie.get("info_hunter", {}),
        spy_out=dossie.get("spy", {}),
        strategist_out=dossie.get("strategist", {}),
        validator_out=dossie.get("validator", {}),
        scout_meta=dossie.get("scout_meta", {}),
    )

    html_path = json_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"✅ HTML gerado: {html_path}")
    print(f"\n📊 Abra no navegador:")
    print(f"   start {html_path}")


if __name__ == "__main__":
    main()
