"""Template de landing page de parceria estratégica / oferta high-ticket.

Estrutura validada (9 seções) — Cookia preenche os placeholders com dados do dossiê:
- {{PERSONA_NOME}}        — nome da persona escolhida
- {{PERSONA_DESC}}        — descrição da persona (1 linha)
- {{DOR_CENTRAL}}         — dor principal extraída do Analyst (rank 1 da persona)
- {{VOCAB_PUBLICO}}       — vocabulário real do público (top termos)
- {{OFERTA_NOME}}         — oferta principal escolhida
- {{OFERTA_PROMESSA}}     — promessa numérica da oferta
- {{OFERTA_TICKET}}       — ticket da oferta
- {{HOOK_PRINCIPAL}}      — hook de venda
- {{CREDENCIAIS}}         — bloco de credenciais (manual; placeholder se vazio)
- {{ANTI_FIT_BULLETS}}    — bullets de quem NÃO é fit (4-6 linhas)
- {{FIT_BULLETS}}         — bullets de quem É fit (4-6 linhas)
"""

LANDING_TEMPLATE = """# PÁGINA DE CAPTURA — {{OFERTA_NOME}}

## SEÇÃO 1: HEADLINE + SUBHEADLINE

**HEADLINE:**
{{HEADLINE_SECAO_1}}

**SUBHEADLINE:**
{{SUBHEADLINE_SECAO_1}}

[ BOTÃO CTA: Quero saber mais ]

---

## SEÇÃO 2: AGITAÇÃO DA DOR (The Gap)

Se isso parece familiar, continue lendo:

{{AGITACAO_DOR}}

---

## SEÇÃO 3: DIAGNÓSTICO CLARO (This Is Why)

Aqui está a verdade que ninguém te contou:

{{DIAGNOSTICO}}

Você precisa de alguém que **{{MECANISMO_RESUMO}}**.

---

## SEÇÃO 4: SOLUÇÃO ÚNICA (The Mechanism)

Como funciona:

{{COMO_FUNCIONA}}

**O que VOCÊ recebe:**
{{O_QUE_RECEBE}}

**O que VOCÊ entrega:**
{{O_QUE_ENTREGA}}

---

## SEÇÃO 5: PROVA IRREFUTÁVEL (Credibilidade)

{{CREDENCIAIS}}

---

## SEÇÃO 6: QUEM É O FIT PERFEITO (Qualificação)

Essa oferta é para você SE:

{{FIT_BULLETS}}

---

## SEÇÃO 7: ANTI-FIT (Desqualificação Estratégica)

Essa oferta NÃO é para você se:

{{ANTI_FIT_BULLETS}}

Se for o caso, tudo bem — mas essa parceria não vai funcionar.

---

## SEÇÃO 8: CTA FINAL

{{CTA_BLOCO}}

[ BOTÃO CTA GRANDE: {{CTA_TEXTO}} ]

---

## SEÇÃO 9: P.S. (Último Empurrão)

**P.S.:**
{{POS_SCRIPTUM}}

[ BOTÃO CTA: Aplicar Agora ]
"""


PROMPT_PREENCHER_LANDING = """Você é Copywriter Senior do Cookia. Sua tarefa: pegar a estrutura de landing page abaixo e PREENCHER cada placeholder com base no dossiê real do cliente.

REGRAS:
- Use o vocabulário REAL do público (palavras EXATAS dos sinais coletados)
- NUNCA escreva genérico tipo "transforme sua vida". Sempre concreto, com número e dor específica.
- Português BR, voz direta, sem jargão corporativo
- Cada seção precisa "puxar pra próxima" — leitor avança naturalmente

## DADOS DO DOSSIÊ

### Persona escolhida
- Nome: {persona_nome}
- Descrição: {persona_desc}
- Contexto: {persona_contexto}
- Ticket alvo: {persona_ticket}
- Vocabulário próprio: {persona_vocab}

### Dor central (rank 1 da persona)
- Dor: {dor_central}
- Frase real do público: "{dor_frase}"
- Pain Score: {dor_pain}

### Oferta principal
- Nome: {oferta_nome}
- Promessa: {oferta_promessa}
- Ticket: {oferta_ticket}
- Hook validado: "{hook_principal}"
- Diferencial: {oferta_diferencial}
- Formato: {oferta_formato}

### Vocabulário real do público (use nas headlines)
{vocab_block}

## ESTRUTURA A PREENCHER

Retorne JSON puro:
```json
{{
  "headline_secao_1": "Headline de 1 frase forte que crava a dor específica. Sem promessa vaga.",
  "subheadline_secao_1": "Sub de 2-3 linhas que aprofunda a dor + nomeia a solução SEM VENDER ainda. Termina com 3 ganchos curtos separados por ponto.",
  "agitacao_dor": "5-8 parágrafos curtos (1-2 linhas cada) que escancaram o dia-a-dia da persona. Cada parágrafo é um aspecto da dor. Termina com 'E aí você olha pro lado e vê...' criando contraste.",
  "diagnostico": "3-4 linhas começando com 'Você não precisa de mais X'. Negar as soluções erradas que o público já tentou. Termina com 'Você precisa de Y' apresentando o conceito da oferta sem ainda detalhar.",
  "mecanismo_resumo": "1 frase forte descrevendo o que a oferta É (parceiro estratégico / consultor que faz com você / acelerador / etc) sem jargão",
  "como_funciona": "2-3 parágrafos explicando o mecanismo único da oferta. Não é curso, não é mentoria genérica, é X específico.",
  "o_que_recebe": "5-7 bullets com ✅ — entregáveis CONCRETOS que o cliente recebe (não 'transformação' — coisas tangíveis)",
  "o_que_entrega": "3-5 bullets com ✅ — o que o cliente PRECISA fazer/disponibilizar pra dar certo (frequência de encontros, abertura de dados, etc)",
  "fit_bullets": "5-7 bullets com ✅ começando com 'Você já tem...', 'Você quer...', 'Você está aberto a...' — filtros de qualificação positiva",
  "anti_fit_bullets": "5-6 bullets com ❌ começando com 'Você ainda não...', 'Você procura apenas...', 'Você não está aberto a...' — desqualificação estratégica honesta",
  "cta_bloco": "2-3 parágrafos explicando o que acontece quando o lead preenche o formulário (análise pessoal, reunião, sem pressão)",
  "cta_texto": "Texto do botão final (3-5 palavras, ação direta — ex: 'Aplicar para Parceria', 'Quero Conversar')",
  "pos_scriptum": "P.S. de 4-6 linhas em parágrafos curtos. Reconhece o que fez o leitor chegar até aqui, valida o sentimento, e termina convidando pra ação SEM pressão."
}}
```

SOMENTE JSON. Em português BR. Use o vocabulário REAL do público nas headlines/subs."""


def montar_landing_md(template: str, dados: dict, credenciais: str = "") -> str:
    """Substitui {{PLACEHOLDERS}} no template com os dados gerados pelo LLM."""
    out = template
    out = out.replace("{{OFERTA_NOME}}", dados.get("oferta_nome", "Oferta"))
    out = out.replace("{{HEADLINE_SECAO_1}}", dados.get("headline_secao_1", ""))
    out = out.replace("{{SUBHEADLINE_SECAO_1}}", dados.get("subheadline_secao_1", ""))
    out = out.replace("{{AGITACAO_DOR}}", dados.get("agitacao_dor", ""))
    out = out.replace("{{DIAGNOSTICO}}", dados.get("diagnostico", ""))
    out = out.replace("{{MECANISMO_RESUMO}}", dados.get("mecanismo_resumo", ""))
    out = out.replace("{{COMO_FUNCIONA}}", dados.get("como_funciona", ""))
    out = out.replace("{{O_QUE_RECEBE}}", dados.get("o_que_recebe", ""))
    out = out.replace("{{O_QUE_ENTREGA}}", dados.get("o_que_entrega", ""))
    out = out.replace("{{CREDENCIAIS}}", credenciais or "_[adicione aqui suas credenciais: trajetória, números, marcas com quem trabalhou, especializações]_")
    out = out.replace("{{FIT_BULLETS}}", dados.get("fit_bullets", ""))
    out = out.replace("{{ANTI_FIT_BULLETS}}", dados.get("anti_fit_bullets", ""))
    out = out.replace("{{CTA_BLOCO}}", dados.get("cta_bloco", ""))
    out = out.replace("{{CTA_TEXTO}}", dados.get("cta_texto", "Aplicar Agora"))
    out = out.replace("{{POS_SCRIPTUM}}", dados.get("pos_scriptum", ""))
    return out
