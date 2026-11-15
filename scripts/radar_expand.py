"""Expande dossiê existente sem rodar pipeline completo.

Usos:
  python scripts/radar_expand.py mais-ofertas [nicho]
  python scripts/radar_expand.py variar <id_oferta> [nicho]
  python scripts/radar_expand.py explorar-dor <rank> [nicho]
  python scripts/radar_expand.py reprice "R$197" [nicho]
  python scripts/radar_expand.py formato "mentoria" [nicho]

Se [nicho] não for passado, usa o dossiê mais recente.

Cada chamada faz 1 chamada ao Claude Sonnet (sem coleta). Confira o gasto real no painel da Anthropic.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.strip().partition("=")
            os.environ.setdefault(k, v.strip().strip('"').strip("'"))

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("❌ ANTHROPIC_API_KEY não setada.")
    sys.exit(1)

from radar_de_demanda.agents.expander import mais_ofertas, variar, explorar_dor, reprice, reformatar

DOSSIES_DIR = ROOT / "data" / "dossies"


def _localiza_dossie(nicho: str | None) -> Path:
    candidatos = sorted(DOSSIES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    candidatos = [p for p in candidatos if p.stat().st_size > 100]
    if not candidatos:
        print(f"❌ Nenhum dossiê JSON em {DOSSIES_DIR}. Rode `radar_run.py` primeiro.")
        sys.exit(1)
    if nicho:
        slug = nicho.lower().replace(" ", "_")
        match = [p for p in candidatos if slug in p.stem.lower()]
        if match:
            return match[0]
        print(f"⚠ Nicho '{nicho}' não encontrado — usando dossiê mais recente.")
    return candidatos[0]


def _imprime(out: dict, titulo: str) -> None:
    print("\n" + "=" * 60)
    print(f"✅ {titulo}")
    print("=" * 60)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def _salva(out: dict, base_path: Path, sufixo: str) -> Path:
    ts = datetime.now().strftime("%H%M")
    novo = base_path.parent / f"{base_path.stem}_{sufixo}_{ts}.json"
    novo.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 Salvo em: {novo.name}")
    return novo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("comando", choices=["mais-ofertas", "variar", "explorar-dor", "reprice", "formato", "order-bump"])
    p.add_argument("arg", nargs="?", default=None, help="Argumento do comando (id, rank, ticket, formato)")
    p.add_argument("nicho", nargs="?", default=None)
    args = p.parse_args()

    dossie_path = _localiza_dossie(args.nicho)
    dossie = json.loads(dossie_path.read_text(encoding="utf-8"))
    print(f"📂 Dossiê base: {dossie_path.name}")

    if args.comando == "mais-ofertas":
        out = mais_ofertas(dossie)
        _imprime(out, "5 novas ofertas")
        _salva(out, dossie_path, "mais_ofertas")
    elif args.comando == "variar":
        if not args.arg:
            print("❌ Faltou ID da oferta. Ex: python scripts/radar_expand.py variar 1")
            sys.exit(1)
        out = variar(dossie, int(args.arg))
        _imprime(out, f"3 variações da oferta #{args.arg}")
        _salva(out, dossie_path, f"variar_{args.arg}")
    elif args.comando == "explorar-dor":
        if not args.arg:
            print("❌ Faltou rank da dor. Ex: python scripts/radar_expand.py explorar-dor 4")
            sys.exit(1)
        out = explorar_dor(dossie, int(args.arg))
        _imprime(out, f"3 ofertas focadas na dor rank #{args.arg}")
        _salva(out, dossie_path, f"dor_{args.arg}")
    elif args.comando == "reprice":
        if not args.arg:
            print("❌ Faltou ticket. Ex: python scripts/radar_expand.py reprice R$197")
            sys.exit(1)
        out = reprice(dossie, args.arg)
        _imprime(out, f"Ofertas reprecificadas pra {args.arg}")
        _salva(out, dossie_path, f"reprice_{args.arg.replace('$','').replace('R','').strip()}")
    elif args.comando == "formato":
        if not args.arg:
            print("❌ Faltou formato. Ex: python scripts/radar_expand.py formato mentoria")
            sys.exit(1)
        out = reformatar(dossie, args.arg)
        _imprime(out, f"Ofertas em formato '{args.arg}'")
        _salva(out, dossie_path, f"formato_{args.arg.replace(' ', '_')}")
    elif args.comando == "order-bump":
        from radar_de_demanda.agents.expander import order_bump
        oferta_id = int(args.arg) if args.arg else None
        out = order_bump(dossie, oferta_id)
        titulo = f"3 order bumps pra oferta #{oferta_id}" if oferta_id else "3 order bumps pra oferta de maior score"
        _imprime(out, titulo)
        _salva(out, dossie_path, f"order_bump_{oferta_id or 'auto'}")


if __name__ == "__main__":
    main()
