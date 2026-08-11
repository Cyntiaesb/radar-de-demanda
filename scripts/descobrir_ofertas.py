"""Cookia — Pipeline standalone: descobre ofertas a partir de sinais reais.

Uso:
    python scripts/descobrir_ofertas.py

Nicho: marketing & vendas (PT-BR). Coleta Google Autocomplete + Reddit BR,
manda pra Claude Sonnet 4.6 categorizar em dores + sugerir ofertas.

Output: data/dossies/marketing_vendas_<ts>.md + .json
"""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8")
except: pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# .env
env_file = ROOT / ".env"
if env_file.exists():
    for L in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in L and not L.strip().startswith("#"):
            k, _, v = L.strip().partition("=")
            os.environ.setdefault(k, v)

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("❌ ANTHROPIC_API_KEY ausente"); sys.exit(1)

from cookia.fontes.google_autocomplete import scrape_google_signals
from cookia.fontes.reddit_br import scrape_reddit

# ──────────────────────────────────────────────────────
# SEEDS: Marketing & Vendas (dor de quem vende/empreende)
# ──────────────────────────────────────────────────────
SEEDS_MARKETING_VENDAS = [
    # Captação / leads
    "como gerar leads qualificados",
    "como prospectar clientes",
    "como aumentar vendas",
    "minha empresa não vende",
    "fluxo de cadência de vendas",
    # Tráfego pago
    "anúncio no google não converte",
    "facebook ads não funciona mais",
    "meta ads caro",
    "como reduzir CPL",
    "tráfego pago para infoproduto",
    # Conteúdo / orgânico
    "como crescer no instagram 2026",
    "instagram não entrega",
    "alcance orgânico caiu",
    "como vender pelo linkedin",
    "como vender no whatsapp",
    # SDR / outbound
    "cold email frio funciona",
    "como abordar lead frio",
    "SDR como prospectar",
    "outbound B2B",
    # CRM / processo
    "qual melhor CRM pequena empresa",
    "funil de vendas como montar",
    "previsibilidade de vendas",
    # IA / automação
    "IA para vendas",
    "automação de marketing pequena empresa",
    "chatgpt para vender",
    "agente de IA para WhatsApp",
    # Posicionamento / oferta
    "como precificar serviço",
    "como criar oferta irresistível",
    "minha oferta não converte",
    "como diferenciar do concorrente",
    # Agência / consultor
    "como contratar agência de marketing",
    "agência de marketing entregou pouco",
    "consultor de vendas vale a pena",
]

REDDIT_QUERIES = [
    "como vender mais",
    "minha empresa não vende",
    "gerar leads",
    "agência de marketing",
    "anúncio não converte",
    "como prospectar B2B",
    "instagram não entrega",
    "IA para vendas",
]

REDDIT_SUBS = [
    "empreendedorismo", "brasil", "brasilivre", "investimentos",
    "marketing", "vendas",
]

# ──────────────────────────────────────────────────────
PROMPT_ANALISE = """Você é analista sênior de demanda B2B no Brasil.

Recebeu {n_google} sinais do Google Autocomplete BR e {n_reddit} posts/comentários do Reddit BR sobre **marketing e vendas**.

Sua tarefa: extrair **OFERTAS COMERCIALIZÁVEIS** com base em dor real, não em jargão.

═══════════════════════════════════════════
SINAIS GOOGLE (top 80)
═══════════════════════════════════════════
{google_sample}

═══════════════════════════════════════════
SINAIS REDDIT (top 40, mais votados)
═══════════════════════════════════════════
{reddit_sample}

═══════════════════════════════════════════
TAREFA
═══════════════════════════════════════════
1. Identifique **8 a 12 SUB-DORES** distintas (não genéricas como "vender mais"; específicas como "anúncio Meta caiu performance pós-iOS17")
2. Pra cada sub-dor, sugira **1 OFERTA** comercializável (serviço, produto, treinamento, SaaS)
3. Estime **prontidão de mercado** (Alta / Média / Baixa) — quanto a pessoa já está procurando solução paga
4. Sugira **ângulo de hook** (1 frase em PT-BR usando vocabulário REAL dos sinais)

OUTPUT: APENAS JSON VÁLIDO no formato:
{{
  "resumo_executivo": "3-4 frases descrevendo o macro-padrão observado nos sinais",
  "sub_dores": [
    {{
      "nome": "Nome curto e específico da sub-dor",
      "evidencia": ["sinal 1 que prova", "sinal 2", "sinal 3"],
      "vocabulario_real": ["palavra/frase exata usada pelo público"],
      "oferta_sugerida": {{
        "nome": "Nome comercial da oferta",
        "tipo": "serviço | infoproduto | SaaS | treinamento | consultoria",
        "promessa_outcome": "1 frase no formato 'Em [prazo], [verbo sensorial] [estado novo]'",
        "preco_sugerido_brl": "faixa BRL estimada (ex: '497-997')",
        "publico_alvo": "quem compraria"
      }},
      "prontidao_mercado": "Alta | Média | Baixa",
      "hook_proposto": "Frase de abertura usando vocabulário real"
    }}
  ],
  "top_3_apostas": ["nome da sub-dor #1 mais promissora", "#2", "#3"],
  "observacoes_estrategicas": "1 parágrafo com insights cruzados (ex: 'duas dores convergem em X')"
}}"""


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_dir = ROOT / "data" / "dossies"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = f"marketing_vendas_{ts}"

    print(f"🚀 Cookia — descoberta de ofertas: marketing & vendas")
    print(f"📂 Output base: {out_dir / slug}\n")

    # ── 1. Google Autocomplete ───────────────────────────
    print(f"━━━ Etapa 1/3: Google Autocomplete ({len(SEEDS_MARKETING_VENDAS)} seeds, depth=2) ━━━")
    t0 = time.time()
    google_sinais = scrape_google_signals(SEEDS_MARKETING_VENDAS, depth=2, delay=0.20)
    print(f"  ✓ {len(google_sinais)} sinais únicos em {time.time()-t0:.1f}s\n")

    # ── 2. Reddit ─────────────────────────────────────────
    print(f"━━━ Etapa 2/3: Reddit BR ({len(REDDIT_QUERIES)} queries × {len(REDDIT_SUBS)} subs) ━━━")
    t0 = time.time()
    reddit_sinais = scrape_reddit(
        REDDIT_QUERIES, subreddits=REDDIT_SUBS,
        posts_per_query=10, comments_per_post=2, delay=0.8,
    )
    print(f"  ✓ {len(reddit_sinais)} posts/coments em {time.time()-t0:.1f}s\n")

    # Salva raw
    raw = {
        "ts": ts, "nicho": "marketing_vendas",
        "seeds_google": SEEDS_MARKETING_VENDAS,
        "queries_reddit": REDDIT_QUERIES,
        "google_sinais": google_sinais,
        "reddit_sinais": reddit_sinais,
    }
    (out_dir / f"{slug}_raw.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  💾 raw salvo: {slug}_raw.json")

    # ── 3. Análise com Claude ─────────────────────────────
    print(f"\n━━━ Etapa 3/3: Análise Claude Sonnet 4.6 ━━━")
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Sample pra caber no prompt (ordena reddit por score)
    google_sample = "\n".join(f"- {s['sinal']}" for s in google_sinais[:80])
    reddit_sorted = sorted(reddit_sinais,
                           key=lambda x: x.get("metadata", {}).get("score", 0), reverse=True)
    reddit_sample = "\n".join(
        f"- [{s.get('metadata',{}).get('score',0)}↑] {s['texto'][:300]}"
        for s in reddit_sorted[:40]
    )

    prompt = PROMPT_ANALISE.format(
        n_google=len(google_sinais),
        n_reddit=len(reddit_sinais),
        google_sample=google_sample,
        reddit_sample=reddit_sample,
    )

    t0 = time.time()
    msg = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"  ✓ Claude respondeu em {time.time()-t0:.1f}s ({msg.usage.input_tokens}in / {msg.usage.output_tokens}out)")

    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        analise = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON inválido — salvando raw text: {e}")
        (out_dir / f"{slug}_analise_RAW.txt").write_text(text, encoding="utf-8")
        return

    (out_dir / f"{slug}_analise.json").write_text(
        json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Markdown dossier ─────────────────────────────────
    md = [f"# Dossiê Cookia — Marketing & Vendas BR",
          f"_{datetime.now().strftime('%Y-%m-%d %H:%M')}_",
          "",
          f"**Sinais coletados:** {len(google_sinais)} Google + {len(reddit_sinais)} Reddit",
          "",
          "## Resumo executivo",
          analise.get("resumo_executivo", "—"),
          "",
          f"## Top 3 apostas",
          ]
    for i, t in enumerate(analise.get("top_3_apostas", []), 1):
        md.append(f"{i}. **{t}**")
    md.append("")
    md.append("## Sub-dores e ofertas")
    for sd in analise.get("sub_dores", []):
        o = sd.get("oferta_sugerida", {})
        md += [
            f"### {sd.get('nome','—')}",
            f"- **Prontidão:** {sd.get('prontidao_mercado','—')}",
            f"- **Vocabulário real:** {', '.join(sd.get('vocabulario_real', []))}",
            f"- **Evidência:**",
            *[f"  - _{e}_" for e in sd.get("evidencia", [])],
            "",
            f"**💡 Oferta sugerida — {o.get('nome','—')}** ({o.get('tipo','—')})",
            f"- Promessa: {o.get('promessa_outcome','—')}",
            f"- Preço: R$ {o.get('preco_sugerido_brl','—')}",
            f"- Público: {o.get('publico_alvo','—')}",
            "",
            f"**🎣 Hook:** {sd.get('hook_proposto','—')}",
            "",
            "---",
            "",
        ]
    md.append("## Observações estratégicas")
    md.append(analise.get("observacoes_estrategicas", "—"))

    md_path = out_dir / f"{slug}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"\n✅ Dossiê: {md_path}")
    print(f"   JSON:   {out_dir / f'{slug}_analise.json'}")
    print(f"\n📊 Encontradas {len(analise.get('sub_dores', []))} sub-dores com ofertas.")


if __name__ == "__main__":
    main()
