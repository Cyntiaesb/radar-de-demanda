"""Motor de geração de copy/ads consumindo dossiê Radar de Demanda.

Carrega prompts .md de .claude/skills/radar-copy/prompts/ e radar-ads/prompts/,
preenche variáveis com campos do dossiê, e chama Claude pra gerar variações.

Uso:
    from radar_de_demanda.copy_outcome import render
    output = render("headline-landing", dossie_path="data/dossies/advocacia_2026-05-15.json")
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / ".claude" / "skills"
DOSSIE_DIR = ROOT / "data" / "dossies"

PACKS = {
    "copy": SKILLS_DIR / "radar-copy" / "prompts",
    "ads": SKILLS_DIR / "radar-ads" / "prompts",
}


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-ish frontmatter (id, consome, output, estagio)."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    meta_raw, body = match.groups()
    meta: dict = {}
    for line in meta_raw.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [item.strip() for item in v[1:-1].split(",") if item.strip()]
        meta[k.strip()] = v
    return meta, body.strip()


def _load_prompt(prompt_id: str) -> tuple[dict, str]:
    for pack_dir in PACKS.values():
        path = pack_dir / f"{prompt_id}.md"
        if path.exists():
            meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
            return meta, body
    raise FileNotFoundError(f"Prompt '{prompt_id}' não encontrado em radar-copy/ ou radar-ads/")


def _load_dossie(path_or_nicho: str | None) -> dict:
    """Aceita: caminho .json, nome do nicho, ou None (pega o mais recente)."""
    if path_or_nicho and path_or_nicho.endswith(".json"):
        return json.loads(Path(path_or_nicho).read_text(encoding="utf-8"))

    candidates = sorted(DOSSIE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Nenhum dossiê em {DOSSIE_DIR}. Rode /radar primeiro.")

    if path_or_nicho:
        candidates = [p for p in candidates if path_or_nicho.lower() in p.stem.lower()] or candidates

    return json.loads(candidates[0].read_text(encoding="utf-8"))


def _fill(body: str, dossie: dict) -> str:
    """Substitui {campo} pelo valor do dossiê (lista → bullets)."""
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        value = dossie.get(key, f"<{key} ausente no dossiê>")
        if isinstance(value, list):
            return "\n".join(f"- {item}" for item in value)
        return str(value)

    return re.sub(r"\{(\w+)\}", replacer, body)


def render(prompt_id: str, dossie_path: str | None = None, *, model: str = "claude-sonnet-4-6") -> str:
    """Renderiza prompt + chama Claude. Retorna texto da resposta."""
    if Anthropic is None:
        raise RuntimeError("Pacote 'anthropic' não instalado. Rode: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY ausente. Configure no .env.")

    meta, body = _load_prompt(prompt_id)
    dossie = _load_dossie(dossie_path)
    filled = _fill(body, dossie)

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": filled}],
    )
    return response.content[0].text


def list_prompts() -> dict[str, list[str]]:
    """Lista IDs disponíveis por pack."""
    return {
        pack: sorted(p.stem for p in pack_dir.glob("*.md"))
        for pack, pack_dir in PACKS.items()
        if pack_dir.exists()
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python -m radar_de_demanda.copy_outcome <prompt-id> [dossiê]")
        print("\nPrompts disponíveis:")
        for pack, ids in list_prompts().items():
            print(f"\n[{pack}]")
            for pid in ids:
                print(f"  - {pid}")
        sys.exit(1)
    print(render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
