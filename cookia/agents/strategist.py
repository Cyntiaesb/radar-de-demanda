"""♟️ Agente Strategist — cruza dor (Analyst) + vencedores (Hunter) + brief.

Gera 5 ideias de produto/oferta pro cliente vender. Cada uma com:
- Encaixe na dor #1
- Diferenciação vs vencedores atuais
- Ticket sugerido (ancorado no Hunter)
- Promessa numérica
- Primeiro passo prático
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

PROMPT_STRATEGIST = """Você é Strategist do Cookia — cria ofertas vendáveis ancoradas em DOR REAL, FÓRMULA VENCEDORA e ÂNGULOS COMPROVADOS por anúncios pagos.

## CONTEXTO DO CLIENTE (quem vai vender)

- Negócio: {negocio}
- Vende hoje: {o_que_vende}
- Cliente alvo do CLIENTE: {cliente_alvo}
- Maior gargalo: {gargalo}

## 🔥 SALTO FINANCEIRO ALMEJADO (CRÍTICO PRA AS OFERTAS)

- **Fatura HOJE:** {faturamento_atual}
- **Quer faturar:** {faturamento_meta}
- **Salto necessário:** {salto_necessario}
- **Ticket sugerido pra meta:** {ticket_sugerido_para_meta}

⚠️ REGRA DE OURO: as ofertas precisam ser CALIBRADAS pro salto.
- Se cliente fatura R$0 e quer R$10k → ofertas de validação + 1ª venda (low-ticket validador)
- Se cliente fatura R$3k e quer R$30k → subir ticket + nova oferta complementar
- Se cliente fatura R$30k e quer R$100k → high-ticket + funil estruturado
- Se cliente fatura R$100k+ → oferta premium + automação + escala

## DOR DETECTADA (do Analyst)

Dores ranqueadas por Pain Score:
{dores_block}

Vocabulário real do público:
{vocab}

## FÓRMULA VENCEDORA — MERCADO LIVRE (Hunter)

Top vencedores no nicho:
{vencedores_block}

Padrões:
- Ticket médio top 10: R${ticket_medio}
- Formato dominante: {formato}
- Ângulo dominante: {angulo}
- Saturação: {saturacao}
- Oportunidade de ataque: {oportunidade}

## FÓRMULA VENCEDORA — HOTMART (InfoHunter — onde o jogo do infoproduto BR acontece)

Top vencedores Hotmart:
{vencedores_hotmart_block}

Padrões Hotmart:
- Ticket médio top 10: R${ticket_medio_hot}
- Ticket sweet spot: {ticket_sweet}
- Formato dominante: {formato_hot}
- Ângulo dominante: {angulo_hot}
- Saturação: {saturacao_hot}
- Oportunidade de ataque Hotmart: {oportunidade_hot}

## INTELIGÊNCIA DE ANÚNCIOS PAGOS (do Spy — Meta Ads Library)

Top anúncios rodando AGORA (ranqueados por dias rodando — quanto mais antigo, mais validado):
{anuncios_block}

Padrões dominantes nos anúncios:
- Ângulo top 1: {angulo_top1}
- Ângulo top 2: {angulo_top2}
- Padrões de hook: {padroes_hook}

🎯 **GAP DE MERCADO IDENTIFICADO (CRUZAR COM DORES!):**
- Ângulo inexplorado: {gap_angulo}
- Por que é oportunidade: {gap_motivo}

## SUA TAREFA — gere 3 BLOCOS estruturados pra entregar caminho COMPLETO:

### BLOCO 1: 5 OFERTAS RASTREÁVEIS (1 produto por dor/gap/ataque)

**Ofertas 1-3:** uma oferta pra cada uma das 3 dores mais quentes (use as 3 primeiras do Analyst). Cada oferta DEVE atacar a dor especificamente — sem desviar pra brainstorm genérico.

**Oferta 4:** ataque pelo GAP DE MERCADO do Spy CRUZADO com uma das dores Bleeding Neck. Ou seja: usa o ângulo que ninguém tá explorando + dor que tá doendo + vocabulário real do público. Essa é a oferta mais inovadora.

**Oferta 5:** ataque direto ao top vencedor do Hunter (mesma dor, ângulo SUPERIOR ao incumbente, ticket competitivo).

### BLOCO 2: ESCALONAMENTO DE FORMATOS (mesma dor #1, 4 produtos diferentes em tickets crescentes)

Pega a DOR #1 (rank 1 do Analyst) e mostra 4 jeitos DIFERENTES de vender a solução, escalonando ticket:
1. **Isca/validador** (R$0-47) — ebook, checklist, mini-aula. Captura lead, testa demanda.
2. **Entrada/transacional** (R$97-297) — curso autoinstrucional, template prático.
3. **Core** (R$497-1.997) — curso com suporte, comunidade, ou consultoria pontual.
4. **Premium/high-ticket** (R$2.997-9.997) — mentoria em grupo, consultoria 1:1, implementação feita.

Cada nível: nome, formato, ticket, promessa específica, quem compra (perfil), tempo de entrega.

### BLOCO 3: MATH DA META + ESCADA ESTRATÉGICA

Conecta as ofertas com o salto financeiro REAL do cliente:

**Math da meta** — pega o `faturamento_meta` e calcula 3 caminhos numéricos pra chegar lá:
- Ex: "Meta R$30k/mês = (a) 60 vendas × R$497 OU (b) 30 vendas × R$997 OU (c) 6 vendas × R$5k mentoria"
- Mostra qual caminho é mais realista pro estágio dele (fatura atual)

**Escada estratégica** — sequência de 3 movimentos nos próximos 90 dias:
- Mês 1: qual oferta lançar primeiro e por quê (geralmente validador ou core mais defensivo)
- Mês 2: qual adicionar depois pra escalar
- Mês 3: qual high-ticket abrir quando tiver tração

Sempre amarra com a meta: "isso te leva de R$X → R$Y/mês se converter Z%".

## Regras adicionais

- Ticket alinhado com mercado (varie ±50% do ticket_medio do Hunter)
- Use ângulos comprovados pelos anúncios com `dias_rodando >= 60` (sinal de profitabilidade)
- Promessa numérica concreta (X em Y dias)
- Primeiro passo prático que cliente faz amanhã
- Use vocabulário_real nos hooks (palavras EXATAS, não polidas)

## OUTPUT (JSON puro)

```json
{{
  "ofertas": [
    {{
      "id": 1,
      "tipo": "dor_direta_1 | dor_direta_2 | dor_direta_3 | gap_de_mercado | ataque_ao_top_vencedor",
      "nome": "Nome vendável (não genérico)",
      "dor_atacada": "rank N — frase da dor",
      "angulo_usado": "qual ângulo (transformação | autoridade | atalho | medo | curiosidade | etc) — preferir os comprovados por anúncios +60d",
      "vencedor_referencia": "qual top seller (Hunter) ou anúncio (Spy) é o benchmark",
      "diferencial": "1 parágrafo: o que faz essa oferta superar o referência",
      "formato": "curso online|mentoria|software|template|consultoria|produto físico|outro",
      "ticket_sugerido": "R$497 OU 'R$197 + R$97/mês'",
      "promessa_numerica": "outcome com número e timeline",
      "publico_alvo": "1 linha quem é o comprador ideal",
      "primeiro_passo_amanha": "ação concreta que cliente faz nas próximas 24h pra começar",
      "hook_de_venda": "1 frase pra usar em landing/anúncio (com vocabulário cru do público)",
      "vocabulario_aplicado": ["3-5 termos do vocabulário real usados na oferta"]
    }}
    // EXATAMENTE 5 ofertas
  ],
  "escalonamento_formatos": {{
    "dor_focada": "rank 1 — frase da dor #1 do Analyst",
    "niveis": [
      {{"nivel": "isca", "nome": "...", "formato": "ebook|checklist|mini-aula|...", "ticket": "R$0-47", "promessa": "...", "perfil_comprador": "...", "tempo_entrega": "..."}},
      {{"nivel": "entrada", "nome": "...", "formato": "curso autoinstrucional|template|...", "ticket": "R$97-297", "promessa": "...", "perfil_comprador": "...", "tempo_entrega": "..."}},
      {{"nivel": "core", "nome": "...", "formato": "curso com suporte|comunidade|consultoria pontual|...", "ticket": "R$497-1997", "promessa": "...", "perfil_comprador": "...", "tempo_entrega": "..."}},
      {{"nivel": "premium", "nome": "...", "formato": "mentoria 1:1|implementação feita|done-with-you|...", "ticket": "R$2997-9997", "promessa": "...", "perfil_comprador": "...", "tempo_entrega": "..."}}
    ]
  }},
  "math_da_meta": {{
    "faturamento_atual": "{faturamento_atual}",
    "faturamento_meta": "{faturamento_meta}",
    "caminhos": [
      {{"opcao": "A", "descricao": "ex: 60 vendas × R$497", "ticket": "R$497", "vendas_por_mes": 60, "viabilidade": "alta|média|baixa", "porque": "1 linha"}},
      {{"opcao": "B", "descricao": "ex: 30 vendas × R$997", "ticket": "R$997", "vendas_por_mes": 30, "viabilidade": "...", "porque": "..."}},
      {{"opcao": "C", "descricao": "ex: 6 vendas × R$5k mentoria", "ticket": "R$5000", "vendas_por_mes": 6, "viabilidade": "...", "porque": "..."}}
    ],
    "caminho_recomendado": "A|B|C — qual é mais realista dado o estágio atual e por quê"
  }},
  "escada_estrategica": {{
    "horizonte": "90 dias",
    "mes_1": {{"oferta": "qual id ou nivel lançar primeiro", "motivo": "porque essa antes das outras", "meta_faturamento": "R$X"}},
    "mes_2": {{"oferta": "...", "motivo": "...", "meta_faturamento": "R$X acumulado"}},
    "mes_3": {{"oferta": "...", "motivo": "...", "meta_faturamento": "R$Y acumulado — atinge a meta?"}}
  }}
}}
```

REGRAS FINAIS:
- Português BR
- NÃO copie o vencedor atual — diferencie via ângulo
- SOMENTE JSON, sem markdown ao redor"""


def strategist(
    brief: dict,
    analyst_out: dict,
    hunter_out: dict,
    spy_out: dict | None = None,
    *,
    info_hunter_out: dict | None = None,
    focused_dor_ranks: list[int] | None = None,
    focused_persona: dict | None = None,
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Combina Analyst + Hunter (ML) + InfoHunter (Hotmart) + Spy + Brief em 5 ofertas.

    Se focused_dor_ranks for passado, gera ofertas SOMENTE pras dores escolhidas
    (modo Discovery — cliente filtrou após Analyst).
    """
    print("\n♟️  [Strategist] Cruzando dor + ML + Hotmart + anúncios + brief...")
    spy_out = spy_out or {}
    info_hunter_out = info_hunter_out or {}
    if focused_dor_ranks:
        print(f"    🎯 Modo Discovery: focando nas dores rank {focused_dor_ranks}")

    dores_full = analyst_out.get("dores", [])[:10]
    if focused_dor_ranks:
        dores = [d for d in dores_full if d.get("rank") in focused_dor_ranks]
        if not dores:
            dores = dores_full
    else:
        dores = dores_full
    dores_block = "\n".join(
        f"- Rank {d.get('rank')}: {d.get('dor')} (Pain Score: {d.get('pain_score')}) "
        f"- '{d.get('frase_real_publico', '')}'"
        for d in dores
    )

    instrucao_focus = ""
    if focused_persona:
        nome_p = focused_persona.get("nome", "?")
        desc_p = focused_persona.get("descricao_uma_linha", "?")
        contexto_p = focused_persona.get("contexto", "?")
        ticket_p = focused_persona.get("ticket_alvo_estimado", "?")
        vocab_p = ", ".join(focused_persona.get("vocabulario_proprio", [])[:8])
        oport_p = focused_persona.get("oportunidade_sintese", "?")
        instrucao_focus += (
            f"\n\n🎯 **PERSONA ESCOLHIDA PELO CLIENTE — FOCO ABSOLUTO:**\n"
            f"- Nome: {nome_p}\n"
            f"- Descrição: {desc_p}\n"
            f"- Contexto: {contexto_p}\n"
            f"- Ticket alvo realista: {ticket_p}\n"
            f"- Vocabulário próprio: {vocab_p}\n"
            f"- Oportunidade comercial: {oport_p}\n\n"
            f"⚠️ TODAS as ofertas precisam falar com ESSA persona específica. "
            f"NÃO crie ofertas pra outras personas que apareceram na análise — "
            f"o cliente escolheu atacar SÓ essa. Use o vocabulário próprio dela nos hooks."
        )
    if focused_dor_ranks:
        instrucao_focus += (
            f"\n\n🎯 **DORES FOCADAS rank {focused_dor_ranks}** — "
            f"ignore as outras dores. Gere as 5 ofertas EXCLUSIVAMENTE em cima dessas dores. "
            f"Se for menos de 3 dores escolhidas, gere variações angulares (mesma dor, ângulos diferentes)."
        )

    vocab = ", ".join(analyst_out.get("vocabulario_real", [])[:15])

    vencedores = hunter_out.get("top_vencedores", [])[:5]
    vencedores_block = "\n".join(
        f"- '{v.get('titulo')}' | R${v.get('ticket')} | vendidos: {v.get('vendidos')} "
        f"| ângulo: {v.get('angulo')}"
        for v in vencedores
    ) or "(sem vencedores detectados)"

    formula = hunter_out.get("fórmula_vencedora", {})

    # InfoHunter (Hotmart)
    top_hot = info_hunter_out.get("top_vencedores_hotmart", [])[:6]
    vencedores_hot_block = "\n".join(
        f"- '{v.get('titulo')}' | R${v.get('ticket')} | rating: {v.get('rating', '?')} | "
        f"formato: {v.get('formato', '?')} | ângulo: {v.get('angulo', '?')}"
        for v in top_hot
    ) or "(Hotmart bloqueou scraping — abrir URLs manualmente)"
    formula_hot = info_hunter_out.get("formula_vencedora_hotmart", {})

    top_ads = spy_out.get("top_anuncios", [])[:6]
    anuncios_block = "\n".join(
        f"- '{a.get('texto_resumido', '?')}' | página: {a.get('pagina', '?')} | "
        f"dias: {a.get('dias_rodando', '?')} ({a.get('validacao', '?')}) | "
        f"ângulo: {a.get('angulo', '?')} | hook: '{a.get('hook', '?')}'"
        for a in top_ads
    ) or "(nenhum anúncio capturado — scraping bloqueado)"

    padroes = spy_out.get("padroes_dominantes", {})
    gap = spy_out.get("gap_de_mercado", {})

    prompt = PROMPT_STRATEGIST.format(
        negocio=brief.get("negocio", "?"),
        o_que_vende=brief.get("o_que_vende", "?"),
        cliente_alvo=brief.get("cliente_alvo", "?"),
        gargalo=brief.get("gargalo", "?"),
        faturamento_atual=brief.get("faturamento_atual", "não informado"),
        faturamento_meta=brief.get("faturamento_meta", "não informado"),
        salto_necessario=brief.get("salto_necessario", "não informado"),
        ticket_sugerido_para_meta=brief.get("ticket_sugerido_para_meta", "não informado"),
        dores_block=dores_block,
        vocab=vocab,
        vencedores_block=vencedores_block,
        ticket_medio=formula.get("ticket_medio_top_10", "?"),
        formato=formula.get("formato_dominante", "?"),
        angulo=formula.get("angulo_dominante", "?"),
        saturacao=formula.get("saturacao", "?"),
        oportunidade=formula.get("oportunidade_de_ataque", "?"),
        vencedores_hotmart_block=vencedores_hot_block,
        ticket_medio_hot=formula_hot.get("ticket_medio_top_10", "?"),
        ticket_sweet=formula_hot.get("ticket_sweet_spot", "?"),
        formato_hot=formula_hot.get("formato_dominante", "?"),
        angulo_hot=formula_hot.get("angulo_dominante", "?"),
        saturacao_hot=formula_hot.get("saturacao", "?"),
        oportunidade_hot=formula_hot.get("oportunidade_de_ataque", "?"),
        anuncios_block=anuncios_block + instrucao_focus,
        angulo_top1=padroes.get("angulo_top_1", "?"),
        angulo_top2=padroes.get("angulo_top_2", "?"),
        padroes_hook=", ".join(padroes.get("padroes_de_hook", [])[:3]) or "?",
        gap_angulo=gap.get("angulo_inexplorado", "(não detectado)"),
        gap_motivo=gap.get("porque_oportunidade", "(análise manual recomendada)"),
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(model=model, max_tokens=8000, messages=[{"role": "user", "content": prompt}])
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()

    out = json.loads(raw)
    n_ofertas = len(out.get('ofertas', []))
    n_niveis = len(out.get('escalonamento_formatos', {}).get('niveis', []))
    n_caminhos = len(out.get('math_da_meta', {}).get('caminhos', []))
    print(f"    ✓ {n_ofertas} ofertas + {n_niveis} níveis de escalonamento + {n_caminhos} caminhos de meta")
    return out
