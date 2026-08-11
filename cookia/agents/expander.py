"""🔄 Expander — gera variações sobre dossiê existente (sem rodar pipeline completo).

5 modos:
  mais_ofertas(): 5 ofertas novas com ângulos diferentes das primeiras
  variar(N): 3 variações da oferta #N
  explorar_dor(N): ofertas focadas numa dor que não foi atacada
  reprice(ticket): regenera ofertas no ticket alvo
  reformatar(formato): regenera ofertas em formato específico

Cada modo custa ~R$3-5 (só Sonnet). NÃO roda Scout/Analyst/Hunter/etc.
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic


def _carrega_dossie(json_path: str) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def _call_sonnet(prompt: str, max_tokens: int = 4096, model: str = "claude-sonnet-4-6") -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
    return json.loads(raw)


def _contexto_base(dossie: dict) -> str:
    """Monta contexto resumido do dossiê pra colar em qualquer prompt."""
    brief = dossie.get("brief", {})
    analyst = dossie.get("analyst", {})
    dores = analyst.get("dores", [])[:10]
    dores_str = "\n".join(f"- Rank {d.get('rank')} (Pain {d.get('pain_score')}): {d.get('dor')} — '{d.get('frase_real_publico', '')[:80]}'" for d in dores)
    vocab = ", ".join(analyst.get("vocabulario_real", [])[:15])
    return f"""## Brief
- Negócio: {brief.get('negocio', '?')}
- Faturamento atual → meta: {brief.get('faturamento_atual', '?')} → {brief.get('faturamento_meta', '?')}
- Salto: {brief.get('salto_necessario', '?')}
- Canal: {brief.get('canal_principal', '?')}

## Dores ranqueadas
{dores_str}

## Vocabulário cru
{vocab}"""


def mais_ofertas(dossie: dict, model: str = "claude-sonnet-4-6") -> dict:
    """Gera 5 ofertas NOVAS com ângulos diferentes das primeiras 5."""
    print("\n🔄 [Expander] Gerando 5 ofertas adicionais com ângulos diferentes...")
    contexto = _contexto_base(dossie)
    ofertas_existentes = dossie.get("validator", {}).get("ofertas", [])
    ofertas_str = "\n".join(f"- '{o.get('nome')}' atacou rank {o.get('dor_atacada')} com ângulo {o.get('angulo_usado', '?')}" for o in ofertas_existentes)

    prompt = f"""Você é Strategist do Cookia. Cliente já recebeu 5 ofertas e quer MAIS 5 com ângulos diferentes.

{contexto}

## OFERTAS JÁ ENTREGUES (NÃO REPETIR)
{ofertas_str}

## TAREFA

Gere 5 NOVAS ofertas explorando:
- Ângulos não usados antes (se as primeiras foram autoridade/transformação, usar atalho/medo/curiosidade/prova social)
- Dores secundárias da lista (rank 4-10)
- Formatos diferentes (se eram cursos, considerar mentoria/comunidade/template/checklist)
- Tickets variando (uma baixa entrada R$47-97, uma média R$197-397, uma premium R$697+)

Retorne JSON puro com mesma estrutura do Strategist original:
```json
{{
  "ofertas": [
    {{
      "id": 6,
      "tipo": "angulo_novo",
      "nome": "Nome vendável",
      "dor_atacada": "rank N — frase",
      "angulo_usado": "novo ângulo",
      "diferencial": "1 parágrafo",
      "formato": "...",
      "ticket_sugerido": "R$...",
      "promessa_numerica": "...",
      "publico_alvo": "...",
      "primeiro_passo_amanha": "...",
      "hook_de_venda": "..."
    }}
  ]
}}
```

SOMENTE JSON."""
    return _call_sonnet(prompt, model=model)


def variar(dossie: dict, oferta_id: int, model: str = "claude-sonnet-4-6") -> dict:
    """Pega oferta #N e gera 3 variações (mesma dor, ângulos diferentes)."""
    print(f"\n🔄 [Expander] Gerando 3 variações da oferta #{oferta_id}...")
    ofertas = dossie.get("validator", {}).get("ofertas", [])
    oferta = next((o for o in ofertas if o.get("id") == oferta_id), None)
    if not oferta:
        raise ValueError(f"Oferta #{oferta_id} não encontrada no dossiê.")

    contexto = _contexto_base(dossie)
    oferta_json = json.dumps(oferta, ensure_ascii=False, indent=2)

    prompt = f"""Você é Strategist do Cookia.

{contexto}

## OFERTA ORIGINAL (gere 3 variações desta)
{oferta_json}

## TAREFA

Mantenha a MESMA dor e o MESMO público. Mude:
- Ângulo (se era transformação, faça versão de autoridade, atalho ou medo)
- Formato (curso → mentoria → comunidade → template)
- Ticket (baixe 50% E suba 50% pra cobrir faixas)

3 variações totais, cada uma com posicionamento DIFERENTE.

Retorne JSON:
```json
{{
  "variacoes": [
    {{
      "id": "{oferta_id}.A",
      "nome": "Variação com ângulo X",
      "angulo_usado": "novo",
      "ticket_sugerido": "R$...",
      "formato": "...",
      "diferencial": "1 parágrafo destacando o que muda da original",
      "hook_de_venda": "...",
      "primeiro_passo_amanha": "..."
    }}
  ]
}}
```
SOMENTE JSON."""
    return _call_sonnet(prompt, max_tokens=3000, model=model)


def explorar_dor(dossie: dict, dor_rank: int, model: str = "claude-sonnet-4-6") -> dict:
    """Foca em dor que não foi atacada nas 5 ofertas principais."""
    print(f"\n🔄 [Expander] Explorando dor #{dor_rank}...")
    dores = dossie.get("analyst", {}).get("dores", [])
    dor = next((d for d in dores if d.get("rank") == dor_rank), None)
    if not dor:
        raise ValueError(f"Dor rank #{dor_rank} não encontrada.")

    contexto = _contexto_base(dossie)
    dor_json = json.dumps(dor, ensure_ascii=False, indent=2)

    prompt = f"""Você é Strategist do Cookia.

{contexto}

## DOR ESPECÍFICA A EXPLORAR
{dor_json}

## TAREFA

Essa dor não foi atacada nas 5 ofertas principais. Crie 3 ofertas focadas EXCLUSIVAMENTE nela, cada uma com ângulo diferente:
- Oferta 1: ataque direto (low-ticket validador R$47-197)
- Oferta 2: solução completa (curso/mentoria R$297-697)
- Oferta 3: transformação premium (R$997+)

Retorne JSON:
```json
{{
  "ofertas_dor_{dor_rank}": [
    {{
      "id": "D{dor_rank}.1",
      "tipo": "entrada|core|premium",
      "nome": "...",
      "angulo_usado": "...",
      "diferencial": "...",
      "ticket_sugerido": "R$...",
      "hook_de_venda": "...",
      "primeiro_passo_amanha": "..."
    }}
  ]
}}
```
SOMENTE JSON."""
    return _call_sonnet(prompt, max_tokens=3000, model=model)


def reprice(dossie: dict, ticket_alvo: str, model: str = "claude-sonnet-4-6") -> dict:
    """Regenera 5 ofertas no ticket alvo."""
    print(f"\n🔄 [Expander] Regerando ofertas no ticket {ticket_alvo}...")
    contexto = _contexto_base(dossie)
    ofertas_atuais = dossie.get("validator", {}).get("ofertas", [])
    nomes = ", ".join(o.get("nome", "") for o in ofertas_atuais)

    prompt = f"""Você é Strategist do Cookia.

{contexto}

## OFERTAS ATUAIS
{nomes}

## TAREFA

Regenere 5 ofertas — TODAS no ticket alvo: **{ticket_alvo}**.

Cada oferta deve:
- Calibrar formato/entrega/promessa pro ticket exato
- Manter a dor atacada das originais quando possível
- Ajustar profundidade (R$47 = checklist, R$297 = curso curto, R$997 = mentoria com call)

Retorne JSON mesma estrutura do Strategist:
```json
{{
  "ofertas_repricadas": [...]
}}
```
SOMENTE JSON."""
    return _call_sonnet(prompt, model=model)


def order_bump(dossie: dict, oferta_id: int | None = None, model: str = "claude-sonnet-4-6") -> dict:
    """Gera 3 order bumps (oferta complementar no checkout) pra uma oferta principal.

    Order bump = item de R$27-97 oferecido no checkout depois que o cliente já decidiu
    comprar a oferta principal. Aumenta ticket médio sem fricção.
    """
    ofertas = dossie.get("validator", {}).get("ofertas", []) or dossie.get("strategist", {}).get("ofertas", [])
    if not ofertas:
        raise ValueError("Sem ofertas no dossiê — rode `cookia_run.py` primeiro.")

    if oferta_id is None:
        # pega oferta com maior score (mais provável de virar produto principal)
        oferta = max(ofertas, key=lambda o: o.get("score", 0))
    else:
        oferta = next((o for o in ofertas if o.get("id") == oferta_id), None)
        if not oferta:
            raise ValueError(f"Oferta #{oferta_id} não encontrada.")

    print(f"\n🛒 [Expander] Gerando 3 order bumps pra oferta '{oferta.get('nome','?')}'...")

    contexto = _contexto_base(dossie)
    oferta_json = json.dumps(oferta, ensure_ascii=False, indent=2)

    prompt = f"""Você é Strategist do Cookia, especialista em order bump.

{contexto}

## OFERTA PRINCIPAL (cliente já decidiu comprar essa)
{oferta_json}

## REGRAS DE ORDER BUMP
- Aparece NO CHECKOUT depois que cliente já clicou em "comprar"
- Ticket BAIXO: R$27 a R$97 (não passa de 30% do ticket principal)
- Resolve UM MICRO-PROBLEMA específico que a oferta principal não resolve completamente
- Promessa de 1 frase, copy de 1-2 linhas (sem espaço pra VSL ou página longa)
- Entrega INSTANTÂNEA (template, checklist, plano, mini-aula gravada) — não pode demandar suporte humano
- Toggle "Sim, adicione" / "Não, obrigada" — fricção quase zero
- Foco em GANHO INCREMENTAL pequeno mas óbvio

## TAREFA
Gere 3 order bumps DIFERENTES pra essa oferta. Use o vocabulário real do público.

Retorne JSON puro:
```json
{{
  "oferta_principal": "{oferta.get('nome','?')}",
  "ticket_principal": "{oferta.get('ticket_sugerido','?')}",
  "order_bumps": [
    {{
      "id": "OB1",
      "nome": "Nome curto vendável (max 8 palavras)",
      "tipo": "checklist|template|mini-aula|plano|spreadsheet|swipe-file|script",
      "ticket": "R$47",
      "micro_dor_resolvida": "1 linha — qual dor específica que sobra mesmo depois da oferta principal",
      "promessa": "1 frase — outcome específico do bump",
      "headline_checkout": "1 linha que aparece na caixa de seleção no checkout (max 80 chars)",
      "subheadline_checkout": "1 linha de apoio (max 120 chars)",
      "bullet_1": "benefício 1 (max 60 chars)",
      "bullet_2": "benefício 2 (max 60 chars)",
      "bullet_3": "benefício 3 (max 60 chars)",
      "porque_aceita": "1 parágrafo: por que o cérebro do comprador vai dizer SIM nesse momento específico",
      "vocabulario_usado": ["3-5 termos do vocabulario_real aplicados"]
    }}
  ]
}}
```

REGRAS FINAIS:
- 3 bumps de tipos DIFERENTES (não 3 checklists)
- Tickets escalonados: ex R$47, R$67, R$97
- Português BR, voz do público
- SOMENTE JSON"""
    return _call_sonnet(prompt, max_tokens=3000, model=model)


def reformatar(dossie: dict, formato: str, model: str = "claude-sonnet-4-6") -> dict:
    """Regenera ofertas em formato específico (mentoria, comunidade, ebook, etc)."""
    print(f"\n🔄 [Expander] Regerando ofertas em formato '{formato}'...")
    contexto = _contexto_base(dossie)
    ofertas_atuais = dossie.get("validator", {}).get("ofertas", [])
    nomes = ", ".join(o.get("nome", "") for o in ofertas_atuais)

    prompt = f"""Você é Strategist do Cookia.

{contexto}

## OFERTAS ATUAIS
{nomes}

## TAREFA

Regenere 5 ofertas — TODAS no formato **{formato}**.

Calibre:
- Promessa do formato (curso = conhecimento, mentoria = aceleração, comunidade = continuidade, etc)
- Ticket típico do formato no BR
- Entregáveis específicos
- Primeiro passo do cliente coerente com o formato

Retorne JSON:
```json
{{
  "ofertas_reformatadas": [...]
}}
```
SOMENTE JSON."""
    return _call_sonnet(prompt, model=model)
