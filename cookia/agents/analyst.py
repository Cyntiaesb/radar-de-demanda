"""🧠 Agente Analyst — categoriza sinais e calcula PAIN SCORE.

Killer feature: detecta 'Bleeding Neck' = dor com Pain Score ≥ 80.

Pain Score (0-100) combina:
  - Frequência    (40%) — quantas menções
  - Emocionalidade (30%) — vocabulário emocional, raiva, frustração
  - Urgência       (20%) — sinais de "preciso resolver agora"
  - Dinheiro envolvido (10%) — Reclame Aqui = pessoa já gastou
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

PROMPT = """Você é Analyst do Cookia — especialista em detectar dor SANGRENTA no mercado BR.

Sua tarefa: ler os sinais coletados e ranquear AS 10 DORES MAIS QUENTES com PAIN SCORE 0-100.

## SINAIS COLETADOS

Total: {total} sinais de Google Autocomplete BR + Reddit BR + Reclame Aqui + Mercado Livre + Google Trends.

{signals_block}

## DADOS DE MERCADO

- Mercado Livre (saturação do nicho): {market}
- Google Trends (volume e tendência dos termos seed):
{trends}

## CÁLCULO DO PAIN SCORE

Para cada dor identificada, atribua score 0-100 combinando:
- **Frequência** (40%): aparece em quantos sinais? Quanto mais, maior.
- **Emocionalidade** (30%): vocabulário emocional (raiva, frustração, desespero, "não aguento mais", "perdi dinheiro"). Reclame Aqui pontua mais.
- **Urgência** (20%): sinais de "preciso resolver hoje" vs "estou pesquisando"
- **Dinheiro envolvido** (10%): se aparece em Reclame Aqui ou Mercado Livre, pessoa já tá gastando dinheiro

PAIN SCORE ≥ 80 = 🩸 BLEEDING NECK (dor sangrenta — alguém pagaria pra resolver HOJE)
PAIN SCORE 60-79 = 🔥 quente
PAIN SCORE 40-59 = 🟡 morno
PAIN SCORE < 40 = ❄️ frio (ignorar)

## OUTPUT (JSON puro, sem markdown)

```json
{{
  "dores": [
    {{
      "rank": 1,
      "dor": "1 linha descritiva da dor",
      "frase_real_publico": "frase EXATA do público extraída dos sinais (não inventar)",
      "pain_score": 87,
      "categoria": "bleeding_neck|quente|morno|frio",
      "frequencia": "N menções",
      "emocionalidade": "alta|media|baixa",
      "urgencia": "alta|media|baixa",
      "dinheiro_envolvido": true|false,
      "fontes": ["google", "reddit", "ra", "ml"],
      "evidencia": "2-3 frases REAIS dos sinais que sustentam esse score",
      "persona_id": "id da persona dona dessa dor — DEVE bater com algum dos personas[].id abaixo"
    }}
    // EXATAMENTE 10 dores ranqueadas
  ],
  "personas": [
    {{
      "id": "P1",
      "nome": "Nome curto da persona (3-5 palavras, ex: 'Profissional CLT 35-50 com medo de IA')",
      "descricao_uma_linha": "1 linha completa: quem é, onde está, qual o momento dela",
      "faixa_etaria": "ex: 25-40 anos",
      "contexto": "1 parágrafo: situação de vida, profissão, renda aproximada, o que ela tá tentando resolver",
      "dores_relacionadas_ranks": [1, 4],
      "vocabulario_proprio": ["5-8 expressões EXATAS que ESSA persona usa nos sinais"],
      "oportunidade_sintese": "1 linha: qual oportunidade comercial existe atendendo ESSA persona",
      "ticket_alvo_estimado": "faixa de ticket que essa persona toparia pagar (ex: 'R$197-997')",
      "intensidade_dor": "alta|media|baixa — derive dos pain_scores das dores dela"
    }}
    // 3 a 5 personas distintas extraídas dos sinais
  ],
  "vocabulario_real": ["20 termos/expressões crus do público (palavras EXATAS dos sinais)"],
  "resumo_executivo": "1 parágrafo: quais SÃO as personas detectadas e por que estão distintas (não junte personas que querem coisas diferentes)"
}}
```

REGRA CRÍTICA DE PERSONAS:
- Não force personas a serem genéricas tipo "todos os interessados". Cada persona DEVE ter contexto distinto (profissão, idade, momento de vida, intensidade de dor).
- Toda dor PRECISA ter um persona_id válido. Se 2 dores são do MESMO público com mesmo contexto, agrupe na mesma persona.
- Se houver mais de 5 perfis distintos, pegue os 5 mais quentes (maior intensidade_dor).

REGRAS:
- Use frases REAIS dos sinais, não polidas
- Pain Score deve ser justificado pela evidência
- Pelo menos 2 dores precisam ter Pain Score ≥ 80 (Bleeding Neck) — se não houver dado, marque como "quente" honestamente
- Português BR
- SOMENTE JSON, nada mais"""


def _extrai_texto(sinal: dict) -> str:
    t = sinal.get("texto") or sinal.get("text") or sinal.get("query") or ""
    f = sinal.get("fonte", "?")
    return f"[{f}] {t[:280]}"


def analyst(scout_output: dict, *, model: str = "claude-sonnet-4-6") -> dict:
    """Analisa sinais e retorna 10 dores ranqueadas com Pain Score."""
    print("\n🧠 [Analyst] Calculando Pain Score por dor...")

    signals = scout_output.get("signals", [])
    trends = scout_output.get("trends", {})
    market = scout_output.get("market", {})

    textos = [_extrai_texto(s) for s in signals[:400] if (s.get("texto") or s.get("text"))]
    signals_block = "\n".join(textos)

    trends_block = "\n".join(
        f"  - {termo}: volume_relativo={t.get('volume_relativo')}, "
        f"tendência={t.get('tendencia')}, delta={t.get('delta_pct')}%"
        for termo, t in trends.items()
    ) or "  (sem dados de trends)"

    prompt = PROMPT.format(
        total=len(textos),
        signals_block=signals_block,
        market=json.dumps(market, ensure_ascii=False),
        trends=trends_block,
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
    bleeding = [d for d in out.get("dores", []) if d.get("pain_score", 0) >= 80]
    n_personas = len(out.get("personas", []))
    print(f"    ✓ {len(out.get('dores', []))} dores ranqueadas ({len(bleeding)} 🩸 Bleeding Neck) em {n_personas} personas distintas")
    return out
