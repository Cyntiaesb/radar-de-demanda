"""Orquestrador Agentic do Radar de Demanda.

Roda 5 agentes em sequência:
  🕵️  Scout       → coleta sinais de 5 fontes (Google, Reddit, RA, ML, Trends)
  🧠 Analyst      → calcula Pain Score 0-100 + detecta Bleeding Neck
  🎯 Hunter       → caça top sellers e decodifica fórmula vencedora
  ♟️  Strategist  → cruza dor + vencedores + brief → 5 ofertas vendáveis
  ⚖️  Validator   → atribui Market Viability Score 0-100 a cada oferta

Uso:
  python scripts/radar_brief.py        # uma vez, define brief
  python scripts/radar_run.py "nicho"  # toda execução

Opções:
  --sem-pausa   não faz perguntas no meio (obrigatório dentro do Claude Code;
                ligado sozinho quando o terminal não é interativo)
  --landing     gera também a landing de 9 seções (1 chamada a mais ao Sonnet)
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
    print("❌ ANTHROPIC_API_KEY não setada. Crie um .env (veja .env.example).")
    sys.exit(1)

from radar_de_demanda.seeds import SEEDS
from radar_de_demanda.agents import router, scout, analyst, hunter, info_hunter, spy, strategist, validator
from radar_de_demanda.agents.analyst import SinaisInsuficientes
from radar_de_demanda.agents.landing import landing as gerar_landing_agent
from radar_de_demanda.render_html import render_html
from radar_de_demanda.fontes import apify_fontes


CUSTO_TEXTO = (
    "O custo depende do modelo e do tamanho da coleta. Uma rodada faz 2 chamadas ao Claude Sonnet "
    "(Analyst e Strategist) e de 1 a 4 ao Claude Haiku (Router sempre; Hunter, InfoHunter e Spy só quando "
    "a fonte deles traz dado). Com --landing, mais 1 ao Sonnet. Confira o gasto real no painel da Anthropic "
    "(console.anthropic.com, em Usage). Com APIFY_TOKEN no .env, o Apify cobra à parte, com teto por rodada "
    "(APIFY_TETO_USD, padrão US$ 1,00); o gasto real do Apify sai no fim da rodada e no dossiê."
)


def deve_pausar(brief: dict, sem_pausa: bool, stdin=None) -> bool:
    """Só pausa para perguntar se o brief pede (discovery), a pessoa não pediu --sem-pausa
    e há alguém digitando no terminal (stdin interativo)."""
    if not brief.get("discovery_mode") or sem_pausa:
        return False
    stdin = stdin if stdin is not None else sys.stdin
    try:
        return bool(stdin and stdin.isatty())
    except (AttributeError, ValueError):
        return False


def _intensidade_emoji(intensidade: str) -> str:
    return {"alta": "🩸", "media": "🔥", "baixa": "🟡"}.get((intensidade or "").lower(), "•")


def _pain_emoji(pain: int) -> str:
    return "🩸" if pain >= 70 else "🔥" if pain >= 60 else "🟡"


def discovery_pause(analyst_out: dict) -> tuple[dict | None, list[int] | None]:
    """Modo Discovery em 2 passos:
      1. Cliente escolhe 1 PERSONA entre as detectadas.
      2. Cliente escolhe quais DORES dessa persona atacar (ou todas).

    Retorna (persona_escolhida, ranks_dores_escolhidas).
    Se cliente pular tudo, retorna (None, None) e pipeline ataca todas.
    """
    personas = analyst_out.get("personas", []) or []
    dores_all = analyst_out.get("dores", []) or []

    if not personas:
        print("\n⚠ Analyst não retornou personas — caindo no fluxo antigo de escolha por dor.")
        return _fallback_pick_dores(dores_all)

    # ---- PASSO 1: escolher persona ----
    print("\n" + "=" * 60)
    print("🔍 MODO DISCOVERY — Passo 1/2: escolha o PÚBLICO que você quer atacar")
    print("=" * 60)
    print("\nA pesquisa revelou esses perfis distintos no nicho. Cada um")
    print("precisa de uma OFERTA diferente. Escolha UM pra atacar primeiro:\n")

    for i, p in enumerate(personas, 1):
        emoji = _intensidade_emoji(p.get("intensidade_dor", ""))
        nome = p.get("nome", "?")
        desc = (p.get("descricao_uma_linha") or "")[:120]
        ticket = p.get("ticket_alvo_estimado", "?")
        oport = (p.get("oportunidade_sintese") or "")[:120]
        ndores = len(p.get("dores_relacionadas_ranks", []))
        print(f"  {i}. {emoji} {nome}")
        print(f"     {desc}")
        print(f"     💰 Ticket alvo: {ticket}   |   🎯 {ndores} dor(es) detectada(s)")
        print(f"     💡 {oport}")
        print()

    print("━" * 60)
    print("Qual público você quer atacar?")
    print("  [1,2,3...]  → escolha UM número")
    print("  [enter]     → atacar TODOS (dispersa o foco — não recomendado)")
    print()
    escolha = input("> ").strip()

    if not escolha:
        print("\n✓ Sem foco de persona — Strategist vai gerar 5 ofertas dispersas.")
        return (None, None)

    try:
        idx = int(escolha.strip()) - 1
        if not (0 <= idx < len(personas)):
            raise ValueError
    except ValueError:
        print("⚠ entrada inválida — atacando todas as personas")
        return (None, None)

    persona = personas[idx]
    ranks_da_persona = persona.get("dores_relacionadas_ranks", []) or []
    dores_da_persona = [d for d in dores_all if d.get("rank") in ranks_da_persona]
    if not dores_da_persona:
        # fallback: filtra por persona_id
        pid = persona.get("id")
        dores_da_persona = [d for d in dores_all if d.get("persona_id") == pid]

    print(f"\n✓ Persona escolhida: {persona.get('nome', '?')}")

    if not dores_da_persona:
        print("⚠ Persona escolhida não tem dores mapeadas — Strategist usará todas as dores.")
        return (persona, None)

    # ---- PASSO 2: escolher dores dentro da persona ----
    print("\n" + "=" * 60)
    print(f"🔍 MODO DISCOVERY — Passo 2/2: dores DE {persona.get('nome', '?')}")
    print("=" * 60)
    print("\nEssas são as dores específicas DESSA persona. Em qual focar?\n")

    dores_da_persona = sorted(dores_da_persona, key=lambda d: d.get("pain_score", 0), reverse=True)
    for i, d in enumerate(dores_da_persona, 1):
        pain = d.get("pain_score", 0)
        emoji = _pain_emoji(pain)
        dor_txt = d.get("dor", "?")
        frase = (d.get("frase_real_publico") or "")[:100]
        print(f"  {i}. {emoji} [Pain {pain}] {dor_txt}")
        print(f'     "{frase}"')
        print()

    print("━" * 60)
    print("Em qual quer focar?")
    print("  [1,2]    → focar nas dores escolhidas (cirúrgico)")
    print("  [enter]  → atacar todas as dores dessa persona")
    print()
    escolha2 = input("> ").strip()

    if not escolha2:
        ranks = [d.get("rank") for d in dores_da_persona if d.get("rank") is not None]
        print(f"\n✓ Atacando todas as {len(ranks)} dores de {persona.get('nome', '?')}.")
        return (persona, ranks)

    try:
        indices = [int(x.strip()) - 1 for x in escolha2.split(",") if x.strip()]
        ranks_escolhidos = [
            dores_da_persona[i].get("rank")
            for i in indices
            if 0 <= i < len(dores_da_persona)
        ]
        if ranks_escolhidos:
            print(f"\n✓ Focando nas dores rank: {ranks_escolhidos}")
            return (persona, ranks_escolhidos)
    except (ValueError, IndexError):
        pass

    print("⚠ entrada inválida — atacando todas as dores da persona")
    ranks = [d.get("rank") for d in dores_da_persona if d.get("rank") is not None]
    return (persona, ranks)


def _fallback_pick_dores(dores_all: list[dict]) -> tuple[None, list[int] | None]:
    """Fallback antigo (1 passo, escolhe dores direto) — usado se Analyst não retornar personas."""
    dores = sorted(dores_all, key=lambda d: d.get("pain_score", 0), reverse=True)[:5]
    print("\nDores mais quentes:\n")
    for i, d in enumerate(dores, 1):
        pain = d.get("pain_score", 0)
        print(f'  {i}. {_pain_emoji(pain)} [Pain {pain}] {d.get("dor", "?")}')
        print(f'     "{(d.get("frase_real_publico") or "")[:80]}"')
    escolha = input("\n> ").strip()
    if not escolha:
        return (None, None)
    try:
        idx = [int(x.strip()) - 1 for x in escolha.split(",") if x.strip()]
        ranks = [dores[i].get("rank") for i in idx if 0 <= i < len(dores)]
        return (None, ranks or None)
    except ValueError:
        return (None, None)

BRIEF_PATH = ROOT / "data" / "brief.json"
HIST_DIR = ROOT / "data" / "historico"


def carrega_brief() -> dict:
    if not BRIEF_PATH.exists():
        print(f"❌ Brief não encontrado em {BRIEF_PATH}")
        print("   Rode primeiro: python scripts/radar_brief.py")
        sys.exit(1)
    return json.loads(BRIEF_PATH.read_text(encoding="utf-8"))


def resolve_seeds(nicho: str, brief: dict) -> list[str]:
    slug = nicho.lower().replace(" ", "_")
    seeds: list[str] = []
    for key, terms in SEEDS.items():
        if slug == key or slug in key or key in slug:
            seeds.extend(terms)
            print(f"  ✓ seeds curados: {key} ({len(terms)} termos)")
            break

    termos_brief = brief.get("termos_busca") or ""
    if isinstance(termos_brief, list):
        extras = [str(t).strip() for t in termos_brief if str(t).strip()]
    else:
        extras = [t.strip() for t in str(termos_brief).split(",") if t.strip()]
    extras = [t for t in extras if t.lower() != "a_descobrir_apos_pesquisa"]
    if extras:
        seeds = extras + seeds
        print(f"  ✓ +{len(extras)} termos do brief")

    if not seeds:
        seeds = [nicho]

    seen, uniq = set(), []
    for s in seeds:
        if s.lower() not in seen:
            seen.add(s.lower())
            uniq.append(s)
    return uniq


def render_md(nicho: str, brief: dict, routing: dict, analyst_out: dict, hunter_out: dict, info_hunter_out: dict, spy_out: dict, strategist_out: dict, validator_out: dict, scout_meta: dict) -> str:
    fat_atual = brief.get("faturamento_atual", "?")
    fat_meta = brief.get("faturamento_meta", "?")
    salto = brief.get("salto_necessario", "?")
    persona_escolhida = brief.get("persona_escolhida")

    out = [f"# Dossiê Radar de Demanda — {nicho.title()}"]
    out.append(f"\n> **Negócio:** {brief.get('negocio', '?')}")
    out.append(f"> **Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    fontes_ativas = [k for k, v in routing.get("fontes_ativas", {}).items() if v]
    out.append(f"> **🧭 Router classificou como:** {routing.get('categoria', '?')} — _{routing.get('subcategoria', '')}_")
    out.append(f"> **Fontes ativadas:** {', '.join(fontes_ativas)} | **Sinais:** {scout_meta.get('total_signals')}")
    out.append(f"> **💰 Salto financeiro:** {fat_atual} → {fat_meta} _(salto: {salto})_")

    # ---- INTRO: como o Radar de Demanda chegou nessas conclusões ----
    out.append("\n## 🧭 Como o Radar de Demanda chegou nessas conclusões\n")
    out.append("Esse dossiê não é chute. Cada decisão saiu de um agente especializado cruzando dados reais:")
    out.append(f"")
    out.append(f"1. **Scout** raspou {scout_meta.get('total_signals', '?')} sinais de {len(fontes_ativas)} fontes BR ({', '.join(fontes_ativas)})")
    out.append(f"2. **Analyst** ranqueou as **10 dores mais quentes** por Pain Score 0-100 (frequência 40% + emocionalidade 30% + urgência 20% + dinheiro envolvido 10%) e agrupou em **personas distintas**")
    out.append(f"3. **Hunter** caçou os top vencedores no **Mercado Livre BR** (quem JÁ tá vendendo)")
    out.append(f"4. **InfoHunter** caçou os top infoprodutos em **Hotmart, Kiwify, Braip, Monetizze e Eduzz** (sweet spot de ticket pro infoproduto BR)")
    out.append(f"5. **Spy** espionou anúncios rodando **AGORA** na Meta Ads Library (anúncio com +60 dias = oferta lucrativa validada)")
    out.append(f"6. **Strategist** cruzou tudo isso com a sua meta financeira ({fat_atual} → {fat_meta}) pra gerar ofertas calibradas pro seu salto")
    out.append(f"7. **Validator** atribuiu Market Viability Score 0-100 (Go 🟢 / Yellow 🟡 / Red 🔴) pra cada oferta")
    out.append("")
    if persona_escolhida:
        out.append(f"> 🎯 **Você escolheu atacar a persona:** {persona_escolhida.get('nome', '?')} — todas as ofertas abaixo estão calibradas pra ELA especificamente.\n")

    # ---- PERSONAS ----
    personas = analyst_out.get("personas", []) or []
    if personas:
        out.append("\n## 👥 Personas detectadas na pesquisa\n")
        out.append("Cada persona pediria uma oferta diferente. A pesquisa revelou esses perfis distintos no nicho:\n")
        out.append("| # | Persona | Intensidade | Ticket alvo | Oportunidade comercial |")
        out.append("|---|---|---|---|---|")
        for p in personas:
            emoji = {"alta":"🩸","media":"🔥","baixa":"🟡"}.get((p.get("intensidade_dor") or "").lower(), "•")
            nome = (p.get("nome") or "?")[:50].replace("|", "—")
            oport = (p.get("oportunidade_sintese") or "?")[:80].replace("|", "—")
            out.append(f"| {p.get('id', '?')} | **{nome}** | {emoji} {p.get('intensidade_dor', '?')} | {p.get('ticket_alvo_estimado', '?')} | _{oport}_ |")
        out.append("")

    out.append("\n## 🩸 Bleeding Neck — Dores mais quentes\n")
    out.append("Cada dor abaixo veio de **frases reais** do público nos sinais coletados. Quanto maior o Pain Score, mais 'sangrenta' é a dor — gente disposta a pagar pra resolver HOJE.\n")
    out.append("| Rank | Dor | Pain | Categoria | Frase real do público |")
    out.append("|---|---|---|---|---|")
    for d in analyst_out.get("dores", [])[:10]:
        emoji = "🩸" if d.get("pain_score", 0) >= 80 else "🔥" if d.get("pain_score", 0) >= 60 else "🟡"
        frase = (d.get("frase_real_publico") or "").replace("|", "—")[:100]
        out.append(f"| {d.get('rank')} | {d.get('dor', '?')} | **{d.get('pain_score')}** {emoji} | {d.get('categoria', '?')} | _{frase}_ |")

    out.append(f"\n**Resumo executivo:** {analyst_out.get('resumo_executivo', '?')}\n")

    out.append("\n## 🎯 Reverse Engineer — Top vencedores do nicho\n")
    out.append("| Rank | Produto | Ticket | Vendidos | Formato | Ângulo |")
    out.append("|---|---|---|---|---|---|")
    for v in hunter_out.get("top_vencedores", [])[:10]:
        titulo = (v.get("titulo") or "?")[:60].replace("|", "—")
        out.append(f"| {v.get('rank')} | {titulo} | R${v.get('ticket')} | {v.get('vendidos', '?')} | {v.get('formato', '?')} | {v.get('angulo', '?')} |")

    formula = hunter_out.get("fórmula_vencedora", {})
    out.append(f"\n**Fórmula vencedora:** ticket médio R${formula.get('ticket_medio_top_10', '?')} | "
               f"formato dominante: {formula.get('formato_dominante', '?')} | "
               f"saturação: {formula.get('saturacao', '?')}")
    out.append(f"\n**Oportunidade de ataque:** {formula.get('oportunidade_de_ataque', '?')}\n")

    out.append("\n## 🛒 Top Infoprodutos — Hotmart, Kiwify, Braip, Monetizze, Eduzz\n")
    top_hot = info_hunter_out.get("top_vencedores_hotmart", [])
    if top_hot:
        out.append("| Rank | Produto | Plataforma | Ticket | Rating | Formato | Ângulo |")
        out.append("|---|---|---|---|---|---|---|")
        for v in top_hot[:10]:
            titulo = (v.get("titulo") or "?")[:50].replace("|", "—")
            out.append(f"| {v.get('rank')} | {titulo} | {v.get('plataforma', '?')} | R${v.get('ticket', '?')} | {v.get('rating', '?')} | {v.get('formato', '?')} | {v.get('angulo', '?')} |")
        f_hot = info_hunter_out.get("formula_vencedora_hotmart", {})
        out.append(f"\n**Fórmula vencedora:** ticket sweet spot **{f_hot.get('ticket_sweet_spot', '?')}** | formato dominante: {f_hot.get('formato_dominante', '?')} | saturação: {f_hot.get('saturacao', '?')}")
        out.append(f"\n**Oportunidade de ataque:** {f_hot.get('oportunidade_de_ataque', '?')}\n")
    else:
        out.append("> _Hotmart bloqueou scraping desta vez, e Kiwify/Braip/Monetizze/Eduzz exigem login — abra os links abaixo manualmente._\n")

    urls_por_plataforma: dict[str, list[dict]] = {}
    for u in info_hunter_out.get("urls_busca", []):
        urls_por_plataforma.setdefault(u.get("plataforma", "hotmart"), []).append(u)

    out.append("**🔗 Veja você mesmo (clique pra abrir):**")
    for plataforma, urls in urls_por_plataforma.items():
        out.append(f"\n_{plataforma.title()}:_")
        for u in urls[:5]:
            out.append(f"- [{u.get('query')}]({u.get('url')})")
    out.append("")

    out.append("\n## 🕵️ Espionagem Meta Ads — Anúncios rodando AGORA\n")
    if spy_out.get("scraping_funcionou") and spy_out.get("top_anuncios"):
        out.append("| # | Página | Ângulo | Hook | Formato |")
        out.append("|---|---|---|---|---|")
        for a in spy_out.get("top_anuncios", [])[:10]:
            hook = (a.get("hook") or "")[:60].replace("|", "—").replace("\n", " ")
            out.append(f"| {a.get('rank')} | {a.get('pagina', '?')} | {a.get('angulo', '?')} | _{hook}_ | {a.get('formato_implicito', '?')} |")

        padroes = spy_out.get("padroes_dominantes", {})
        out.append(f"\n**Padrões dominantes:** ângulo top — `{padroes.get('angulo_top_1', '?')}` / `{padroes.get('angulo_top_2', '?')}` | formato — {padroes.get('formato_dominante', '?')}")
        out.append("\n**Padrões de hook que mais aparecem:**\n" + "\n".join(f"- _{h}_" for h in padroes.get("padroes_de_hook", [])))

        gap = spy_out.get("gap_de_mercado", {})
        out.append(f"\n### 🎯 Gap de mercado detectado")
        out.append(f"- **Ângulo inexplorado:** {gap.get('angulo_inexplorado', '?')}")
        out.append(f"- **Por que é oportunidade:** {gap.get('porque_oportunidade', '?')}")
        out.append(f"- **Hook sugerido:** _{gap.get('hook_sugerido', '?')}_")
    else:
        out.append("> _Scraping da Meta bloqueado — abra os links abaixo manualmente pra ver os anúncios._\n")

    out.append("\n**🔗 Veja os anúncios você mesmo (clique pra abrir no Facebook):**")
    for u in spy_out.get("urls_busca", [])[:6]:
        out.append(f"- [{u.get('keyword')}]({u.get('url')})")
    out.append("")

    # ---- MATH DA META + ESCADA ESTRATÉGICA ----
    math = strategist_out.get("math_da_meta") or {}
    escada = strategist_out.get("escada_estrategica") or {}
    escal = strategist_out.get("escalonamento_formatos") or {}

    if math.get("caminhos"):
        out.append("\n## 🧮 Math da Meta — Como chegar em {meta}\n".format(meta=fat_meta))
        out.append(f"Você fatura hoje **{fat_atual}** e quer atingir **{fat_meta}**. Tem 3 caminhos matemáticos pra fazer essa ponte:\n")
        out.append("| Opção | Caminho | Ticket | Vendas/mês | Viabilidade | Por quê |")
        out.append("|---|---|---|---|---|---|")
        for c in math.get("caminhos", []):
            descr = (c.get("descricao") or "?").replace("|", "—")
            porque = (c.get("porque") or "?").replace("|", "—")[:80]
            out.append(f"| **{c.get('opcao','?')}** | {descr} | {c.get('ticket','?')} | {c.get('vendas_por_mes','?')}/mês | {c.get('viabilidade','?')} | _{porque}_ |")
        rec = math.get("caminho_recomendado", "?")
        out.append(f"\n> 🎯 **Caminho recomendado pra você (estágio {salto}):** Opção **{rec}** — é o mais realista dado que você {('está começando do zero' if 'criar' in salto.lower() else 'já tem tração')}.\n")

    if escal.get("niveis"):
        out.append("\n## 🪜 Escalonamento de Formatos — Mesma dor, 4 produtos diferentes\n")
        out.append(f"A dor focada (**{escal.get('dor_focada', '?')}**) pode ser resolvida em formatos diferentes em tickets crescentes. Isso te dá uma **escada de ofertas** — começa barato pra validar, sobe ticket conforme entrega resultado:\n")
        out.append("| Nível | Nome | Formato | Ticket | Promessa | Perfil que compra |")
        out.append("|---|---|---|---|---|---|")
        for n in escal.get("niveis", []):
            nome = (n.get("nome") or "?")[:40].replace("|", "—")
            prom = (n.get("promessa") or "?")[:60].replace("|", "—")
            perfil = (n.get("perfil_comprador") or "?")[:60].replace("|", "—")
            out.append(f"| **{n.get('nivel','?').upper()}** | {nome} | {n.get('formato','?')} | {n.get('ticket','?')} | _{prom}_ | {perfil} |")
        out.append("")

    if escada.get("mes_1"):
        out.append("\n## 📅 Escada Estratégica — Plano de 90 dias\n")
        out.append("Sequência que conecta as ofertas com sua meta. Não é tudo ao mesmo tempo — é um movimento por mês:\n")
        for m_key, m_emoji in [("mes_1", "1️⃣"), ("mes_2", "2️⃣"), ("mes_3", "3️⃣")]:
            m = escada.get(m_key) or {}
            out.append(f"### {m_emoji} Mês {m_key[-1]} — {m.get('oferta', '?')}")
            out.append(f"- **Por que essa primeiro:** {m.get('motivo', '?')}")
            out.append(f"- **Meta de faturamento:** {m.get('meta_faturamento', '?')}\n")
        out.append(f"> ⏱  Em 90 dias, esse plano te leva de **{fat_atual}** a **{escada.get('mes_3', {}).get('meta_faturamento', '?')}** — se a oferta converter em taxas realistas (2-5% em frio, 8-15% em quente).\n")

    out.append("\n## 💰 5 Ofertas Validadas (Score 0-100)\n")
    out.append("As 5 ofertas abaixo são as **cirúrgicas**: cada uma ataca uma dor específica + foi validada pelo Validator. O score 0-100 combina:\n")
    out.append("- **Volume (35%)** — quanta gente busca isso (Google Trends + frequência nos sinais)")
    out.append("- **Ticket (25%)** — quanto se cobra pra essa dor (Hunter + Hotmart)")
    out.append("- **Saturação (25%)** — quão concorrido está (alto = mais difícil entrar)")
    out.append("- **Tendência (15%)** — crescimento nos últimos 90 dias (Google Trends)\n")
    out.append("**Veredito:** 🟢 Go (≥75) | 🟡 cautela (50-74) | 🔴 não recomendo (<50)\n")
    out.append("| # | Oferta | Score | Ticket | Veredito |")
    out.append("|---|---|---|---|---|")
    for of in validator_out.get("ofertas", []):
        nome = (of.get("nome") or "?")[:50]
        out.append(f"| {of.get('id')} | **{nome}** | **{of.get('score')}/100** {of.get('semaforo')} | {of.get('ticket_sugerido')} | {of.get('veredito')} |")

    out.append("\n### Detalhamento por oferta\n")
    for of in validator_out.get("ofertas", []):
        out.append(f"#### {of.get('semaforo')} {of.get('nome')} — Score {of.get('score')}/100\n")
        out.append(f"- **Dor atacada:** {of.get('dor_atacada')}")
        out.append(f"- **Vencedor referência:** {of.get('vencedor_referencia')}")
        out.append(f"- **Diferencial:** {of.get('diferencial')}")
        out.append(f"- **Formato:** {of.get('formato')}")
        out.append(f"- **Ticket:** {of.get('ticket_sugerido')}")
        out.append(f"- **Promessa:** {of.get('promessa_numerica')}")
        out.append(f"- **Público:** {of.get('publico_alvo')}")
        out.append(f"- **Hook:** _{of.get('hook_de_venda')}_")
        out.append(f"- **🚀 Primeiro passo (24h):** {of.get('primeiro_passo_amanha')}")
        b = of.get("score_breakdown", {})
        out.append(f"- **Score breakdown:** volume {b.get('volume')} | ticket {b.get('ticket')} | saturação {b.get('saturacao')} | tendência {b.get('tendencia')}\n")

    gasto = scout_meta.get("apify")
    if gasto:
        partes = ", ".join(f"{k}: US$ {v:.4f}" for k, v in gasto.get("por_fonte", {}).items())
        out.append(f"\n_Apify nesta rodada: US$ {gasto['total_usd']:.4f} (teto US$ {gasto['teto_usd']:.2f})"
                   f"{' — ' + partes if partes else ''}._\n")

    indisponiveis = [v for v in (scout_meta.get("fontes_status") or {}).values() if not v.get("ok")]
    if indisponiveis:
        out.append("\n## 🔗 Fontes indisponíveis hoje — abra à mão\n")
        out.append("Estas fontes bloquearam a coleta automática ou não trouxeram resultado nesta rodada. "
                   "O Radar não tenta contornar bloqueio: abra as buscas abaixo no navegador.\n")
        for v in indisponiveis:
            out.append(f"_{v.get('nome', '?')}:_")
            for l in v.get("links", []):
                out.append(f"- [{l.get('query')}]({l.get('url')})")
            out.append("")
    out.append("\n## 🗣️ Vocabulário real do público\n")
    out.append(", ".join(f"`{t}`" for t in analyst_out.get("vocabulario_real", [])[:25]))

    out.append("\n\n---")
    out.append(f"\n## 📅 Rode de novo em 14-21 dias\n")
    out.append("O mercado BR muda toda semana. Produto que tá 🟡 hoje pode virar 🟢 mês que vem.")
    out.append("Quem roda mensal:")
    out.append("- Pega tendência ANTES da concorrência")
    out.append("- Vê quais ofertas Spy ainda rodam (sinal de profitabilidade contínua)")
    out.append("- Atualiza vocabulário do público (palavras mudam rápido)")
    out.append("- Histórico versionado mostra **o que mudou desde o último run**\n")
    out.append(f"\n💰 _{CUSTO_TEXTO} Sem mensalidade._")
    out.append(f"\n\n🎯 _Próximo passo prático: `/radar-copy <prompt-id>` ou `/radar-ads <prompt-id>` pra gerar copy/anúncio direto do dossiê._")

    out.append(f"\n\n## 🔄 Quer MAIS opções? Use os comandos de expansão (1 chamada ao Sonnet cada)\n")
    out.append("Sem precisar rodar dossiê novo:")
    out.append("- `python scripts/radar_expand.py mais-ofertas` → 5 ofertas novas com ângulos diferentes")
    out.append("- `python scripts/radar_expand.py variar 1` → 3 variações da oferta #1")
    out.append("- `python scripts/radar_expand.py explorar-dor 4` → 3 ofertas focadas na dor #4")
    out.append('- `python scripts/radar_expand.py reprice "R$197"` → reprecifica todas pro novo ticket')
    out.append('- `python scripts/radar_expand.py formato "mentoria"` → regera tudo como mentoria')
    out.append("\n_Brainstorm ilimitado em cima do dossiê que você já gerou._")
    return "\n".join(out)


def render_csv(validator_out: dict) -> str:
    """CSV das 5 ofertas, abrível no Excel/Sheets."""
    linhas = ["id;nome;score;veredito;ticket;dor_atacada;hook;primeiro_passo"]
    for of in validator_out.get("ofertas", []):
        campos = [
            str(of.get("id", "")),
            (of.get("nome") or "").replace(";", ","),
            str(of.get("score", "")),
            (of.get("veredito") or "").replace(";", ","),
            (of.get("ticket_sugerido") or "").replace(";", ","),
            (of.get("dor_atacada") or "").replace(";", ","),
            (of.get("hook_de_venda") or "").replace(";", ","),
            (of.get("primeiro_passo_amanha") or "").replace(";", ","),
        ]
        linhas.append(";".join(campos))
    return "\n".join(linhas)


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("nicho", help="nicho a pesquisar (ex: 'produtividade', 'fitness feminino')")
    p.add_argument("--max-reddit", type=int, default=200)
    p.add_argument("--max-google", type=int, default=300)
    p.add_argument("--max-ra", type=int, default=100)
    p.add_argument("--no-trends", action="store_true", help="pular Google Trends (debug)")
    p.add_argument("--youtube-videos", type=str, default="",
                    help="URLs de vídeo (separadas por vírgula) pra coletar comentários como sinal extra")
    p.add_argument("--sem-pausa", action="store_true",
                   help="não faz perguntas no meio da rodada (use dentro do Claude Code)")
    p.add_argument("--landing", action="store_true",
                   help="gera também a landing de 9 seções (1 chamada a mais ao Sonnet)")
    args = p.parse_args(argv)

    brief = carrega_brief()
    nicho = args.nicho
    nicho_slug = nicho.lower().replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_dir = ROOT / "data" / "dossies"
    out_dir.mkdir(parents=True, exist_ok=True)
    hist_dir = HIST_DIR / nicho_slug
    hist_dir.mkdir(parents=True, exist_ok=True)

    base = out_dir / f"{nicho_slug}_{ts}"
    print(f"\n{'=' * 60}")
    print(f"🚀 RADAR DE DEMANDA — Agent Swarm — {nicho}")
    print(f"{'=' * 60}")
    print(f"📋 Brief: {brief.get('negocio', '?')}")
    print(f"📂 Output: {base}")
    print(f"\n{'─' * 60}")
    print("⏱  TEMPO: este dossiê pode levar vários minutos — não é seu computador")
    print("    travando. Os agentes coletam sinais e cruzam os dados.")
    print(f"\n💰 CUSTO: {CUSTO_TEXTO}")
    print(f"\n🔄 FREQUÊNCIA RECOMENDADA: rode novamente a cada 14-21 dias.")
    print("    O mercado BR muda toda semana — produto que tava 🟡 hoje pode")
    print("    virar 🟢 mês que vem (e vice-versa).")
    print(f"{'─' * 60}\n")

    seeds = resolve_seeds(nicho, brief)

    routing = router(brief, nicho)

    youtube_videos = [u.strip() for u in args.youtube_videos.split(",") if u.strip()] or None

    scout_out = scout(
        seeds,
        routing_config=routing,
        max_google=args.max_google,
        max_reddit=args.max_reddit,
        max_ra=args.max_ra,
        youtube_videos=youtube_videos,
    )
    (base.with_name(f"{nicho_slug}_{ts}_raw.json")).write_text(
        json.dumps(scout_out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    try:
        analyst_out = analyst(scout_out)
    except SinaisInsuficientes as e:
        print(f"\n❌ {e}")
        sys.exit(2)

    focused_ranks = None
    focused_persona = None
    pausar = deve_pausar(brief, args.sem_pausa)
    if brief.get("discovery_mode") and not pausar:
        print("\n⏭  Sem pausa (--sem-pausa ou terminal não interativo): seguindo com todas as personas e dores.")
    if pausar:
        focused_persona, focused_ranks = discovery_pause(analyst_out)
        if focused_persona:
            # Injeta dados da persona no brief antes do Hunter/Spy/Strategist
            brief["persona_escolhida"] = focused_persona
            brief["cliente_alvo"] = focused_persona.get("descricao_uma_linha") or brief.get("cliente_alvo")
            brief["ticket_sugerido_para_meta"] = focused_persona.get("ticket_alvo_estimado") or brief.get("ticket_sugerido_para_meta")

    hunter_out = hunter(nicho, seeds)
    info_hunter_out = info_hunter(nicho, seeds)
    spy_out = spy(nicho, seeds, analyst_out.get("vocabulario_real", []))
    strategist_out = strategist(brief, analyst_out, hunter_out, spy_out,
                                info_hunter_out=info_hunter_out,
                                focused_dor_ranks=focused_ranks,
                                focused_persona=focused_persona)
    validator_out = validator(strategist_out, analyst_out, hunter_out, scout_out.get("trends", {}))

    # Landing de 9 seções: só com --landing (1 chamada a mais ao Sonnet)
    landing_out: dict = {}
    if args.landing:
        landing_out = gerar_landing_agent({
            "analyst": analyst_out,
            "validator": validator_out,
            "strategist": strategist_out,
            "brief": brief,
        })

    dossie = {
        "nicho": nicho,
        "brief": brief,
        "routing": routing,
        "analyst": analyst_out,
        "hunter": hunter_out,
        "info_hunter": info_hunter_out,
        "spy": spy_out,
        "strategist": strategist_out,
        "validator": validator_out,
        "landing": landing_out,
        "scout_meta": {
            "total_signals": len(scout_out.get("signals", [])),
            "trends": scout_out.get("trends", {}),
            "market": scout_out.get("market", {}),
            "fontes_status": scout_out.get("fontes_status", {}),
            "apify": apify_fontes.resumo_gastos() if apify_fontes.token() else None,
        },
        "gerado_em": datetime.now().isoformat(),
    }

    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    csv_path = base.with_suffix(".csv")
    landing_path = base.with_name(base.stem + "_landing.md")
    hist_path = hist_dir / f"{ts}.json"

    json_path.write_text(json.dumps(dossie, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_md(nicho, brief, routing, analyst_out, hunter_out, info_hunter_out, spy_out, strategist_out, validator_out, dossie["scout_meta"]), encoding="utf-8")
    csv_path.write_text(render_csv(validator_out), encoding="utf-8")
    if landing_out.get("markdown"):
        landing_path.write_text(landing_out["markdown"], encoding="utf-8")
    html_path = base.with_suffix(".html")
    html_path.write_text(render_html(nicho, brief, routing, analyst_out, hunter_out, info_hunter_out, spy_out, strategist_out, validator_out, dossie["scout_meta"], landing_out=landing_out), encoding="utf-8")
    hist_path.write_text(json.dumps(dossie, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"✅ Dossiê Agentic gerado:")
    print(f"   📄 {md_path.name}    (humano — abra no Claude Code)")
    print(f"   🎨 {html_path.name}  (dashboard — abra no navegador)")
    if landing_out.get("markdown"):
        print(f"   🪶 {landing_path.name}  (landing 9 seções — cole no Lovable)")
    print(f"   📊 {csv_path.name}   (planilha — abra no Excel)")
    print(f"   🤖 {json_path.name}  (consumido por /radar-copy e /radar-ads)")
    print(f"   📚 historico/{nicho_slug}/{ts}.json")
    print(f"{'=' * 60}")
    print(f"\n{'─' * 60}")
    print("🎯 PRÓXIMOS PASSOS:")
    print(f"   1. Abra o .md no Claude Code Desktop pra ver bonito")
    print(f"   2. Use os links do bloco '🕵️ Espionagem Meta Ads' pra ver")
    print(f"      anúncios reais rodando agora no seu nicho")
    print(f"   3. Pegue uma das ofertas 🟢 Go e execute o '🚀 Primeiro passo (24h)'")
    print(f"   4. Use /radar-copy <prompt-id> pra gerar copy específica")
    print(f"\n📅 LEMBRETE: anote na agenda — rodar de novo em ~15 dias.")
    print("    Demanda BR muda rápido. Quem roda mensal pega oportunidade")
    print("    antes do mercado saturar.")
    print(f"{'─' * 60}")


if __name__ == "__main__":
    main()
