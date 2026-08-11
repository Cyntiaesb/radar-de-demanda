"""Solution-Market Fit Generator — gera oferta única por lead.

Inspirado em Cook.ai (research.trycook.ai). Para cada lead:
- Pega dados do lead (Apify/DB)
- Cruza com sub-tema dor do dossiê Demand Intel
- Considera top concorrente local (se houver)
- Aplica segmento de entrega da SUA empresa (configurável — ver `segmentos`)
- Claude Sonnet gera: promessa outcome + mecanismo único + disconnect hook + battle cards

Uso programático:
    from radar_de_demanda.smf_generator import gerar_oferta
    oferta = gerar_oferta(
        lead, sub_tema, top_concorrente, segmento="S1",
        empresa_nome="Sua Empresa",
        empresa_descricao="agência que vende presença digital para advogados/contadores/nutricionistas em SP",
        segmentos={
            "S1": "sem presença digital (sem site, IG fraco) — entrega: SITE + IG + Blog",
            "S2": "tem site fraco/desatualizado — entrega: REDESIGN + SEO + Blog",
            "S3": "tem site OK, falta automação — entrega: AGENTE WHATSAPP + automação",
        },
    )
"""
from __future__ import annotations
import json
import os
from typing import Any


PROMPT_SMF = """Você é estrategista de oferta B2B para a {empresa_nome} ({empresa_descricao}).

Sua tarefa: gerar uma OFERTA ÚNICA E OUTCOME-BASED para o lead abaixo, cruzando 4 inputs.

═══════════════════════════════════════════
INPUT 1 — DADOS DO LEAD
═══════════════════════════════════════════
Nome: {lead_nome}
Nicho: {lead_nicho}
Cidade: {lead_cidade}
Tem site: {lead_tem_site}
Tem Instagram ativo: {lead_tem_ig}
Reviews Google: {lead_reviews}
Estrelas Google: {lead_estrelas}
Sub-especialidade (se houver): {lead_sub_especialidade}

═══════════════════════════════════════════
INPUT 2 — SUB-TEMA DOR (Demand Intel)
═══════════════════════════════════════════
Sub-tema: {sub_tema_nome}
Volume de sinais: {sub_tema_volume}
Vocabulário real do mercado: {sub_tema_vocab}
Buscas representativas:
{sub_tema_buscas}

═══════════════════════════════════════════
INPUT 3 — TOP CONCORRENTE LOCAL
═══════════════════════════════════════════
Nome: {concorrente_nome}
Reviews: {concorrente_reviews}
Diferencial visível: {concorrente_diferencial}

═══════════════════════════════════════════
INPUT 4 — SEGMENTO DE ENTREGA
═══════════════════════════════════════════
Segmento: {segmento}
Significado dos segmentos:
{segmentos_block}

═══════════════════════════════════════════
REGRAS RÍGIDAS (NÃO QUEBRAR)
═══════════════════════════════════════════
1. PROIBIDO inventar percentuais ("87% fracassam", "73% perdem clientes"). Respeite compliance do setor do lead.
2. PROIBIDO promessa de resultado garantido em volume ("garanto X contratos"). Use linguagem de PROCESSO ("estrutura pra captar", "sistema pra aparecer").
3. Use vocabulário REAL do sub-tema (input 2), não jargão de agência.
4. Promessa deve ser OUTCOME (o que o cliente VAI EXPERIMENTAR), não entregável ("vamos fazer um site").
5. Mecanismo único = a forma específica como a {empresa_nome} resolve. Não pode ser genérico.
6. Disconnect hook = o que a concorrência (agências comuns) FAZ ERRADO e a {empresa_nome} faz diferente.
7. Battle cards = 3 objeções esperadas + resposta de 1 linha cada.

═══════════════════════════════════════════
OUTPUT — APENAS JSON VÁLIDO
═══════════════════════════════════════════
{{
  "promessa_outcome": "1 frase no formato: 'Em [prazo realista], [verbo de experiência sensorial] [estado novo concreto]'. Sem números inventados.",
  "mecanismo_unico": {{
    "nome": "Nome curto e específico do método (3-5 palavras)",
    "explicacao": "2-3 frases explicando COMO funciona, usando vocabulário do sub-tema"
  }},
  "disconnect_hook": "1 frase que contrasta com o que agência comum faz. Formato: 'Agência comum [X errado]. {empresa_nome} [Y diferente].'",
  "battle_cards": [
    {{"objecao": "objeção esperada 1 (palavra do lead)", "resposta": "resposta curta (1 linha)"}},
    {{"objecao": "objeção esperada 2", "resposta": "..."}},
    {{"objecao": "objeção esperada 3", "resposta": "..."}}
  ],
  "alinhamento_sub_tema": "1 linha justificando POR QUE esse sub-tema é a dor mais provável desse lead específico"
}}"""

SEGMENTOS_PADRAO = {
    "S1": "sem presença digital (sem site, IG fraco) — entrega: SITE + IG + Blog",
    "S2": "tem site fraco/desatualizado — entrega: REDESIGN + SEO + Blog",
    "S3": "tem site OK, falta automação — entrega: AGENTE WHATSAPP + automação",
}


def gerar_oferta(
    lead: dict[str, Any],
    sub_tema: dict[str, Any],
    top_concorrente: dict[str, Any] | None,
    segmento: str,
    *,
    empresa_nome: str = "sua empresa",
    empresa_descricao: str = "empresa que resolve a dor mapeada no dossiê Demand Intel",
    segmentos: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Roda Claude Sonnet com o prompt SMF e retorna JSON parseado.

    `empresa_nome`/`empresa_descricao`/`segmentos` descrevem O SEU negócio —
    adapte pro seu nicho e modelo de entrega antes de rodar pra um cliente real.
    """
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    conc = top_concorrente or {}
    buscas = "\n".join(f"  - {b}" for b in sub_tema.get("buscas_representativas", [])[:5])
    segmentos = segmentos or SEGMENTOS_PADRAO
    segmentos_block = "\n".join(f"- {chave} = {desc}" for chave, desc in segmentos.items())

    prompt = PROMPT_SMF.format(
        empresa_nome=empresa_nome,
        empresa_descricao=empresa_descricao,
        lead_nome=lead.get("full_name") or lead.get("nome", "—"),
        lead_nicho=lead.get("niche", "—"),
        lead_cidade=lead.get("location", "—"),
        lead_tem_site="não" if not lead.get("website") else "sim",
        lead_tem_ig="—" if not lead.get("instagram_username") else "sim",
        lead_reviews=lead.get("reviews_count", "—"),
        lead_estrelas=lead.get("rating", "—"),
        lead_sub_especialidade=lead.get("sub_persona") or "—",
        sub_tema_nome=sub_tema.get("nome", "—"),
        sub_tema_volume=sub_tema.get("volume", "—"),
        sub_tema_vocab=", ".join(sub_tema.get("vocabulario_real", [])),
        sub_tema_buscas=buscas,
        concorrente_nome=conc.get("nome", "—"),
        concorrente_reviews=conc.get("reviews", "—"),
        concorrente_diferencial=conc.get("diferencial", "—"),
        segmento=segmento,
        segmentos_block=segmentos_block,
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


if __name__ == "__main__":
    # Smoke test com lead fictício
    import sys, pathlib
    ROOT = pathlib.Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    for L in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in L and not L.strip().startswith("#"):
            k, _, v = L.strip().partition("=")
            os.environ.setdefault(k, v)

    lead = {
        "full_name": "Exemplo Advocacia",
        "niche": "advocacia",
        "location": "São Paulo",
        "website": None,
        "instagram_username": None,
        "reviews_count": 12,
        "rating": 4.8,
        "sub_persona": None,
    }
    # Sub-tema 3 (Site profissional) — match natural pra S1 sem site
    sub_tema = {
        "nome": "Criação e Gestão de Site Profissional",
        "volume": 89,
        "vocabulario_real": ["página de conversão", "SEO jurídico", "landing page de serviços"],
        "buscas_representativas": [
            "site para advogados",
            "como criar site para advogado",
            "site para advogado captar clientes",
            "site para advogados grátis",
            "criar site para advogados wordpress",
        ],
    }
    top_conc = {
        "nome": "Exemplo Concorrente Advogados",
        "reviews": 287,
        "diferencial": "Site com blog SEO ativo + landing por área",
    }
    print("Gerando oferta...")
    oferta = gerar_oferta(
        lead, sub_tema, top_conc, segmento="S1",
        empresa_nome="Sua Empresa",
        empresa_descricao="agência que vende presença digital para advogados/contadores/nutricionistas em SP",
    )
    print(json.dumps(oferta, ensure_ascii=False, indent=2))
