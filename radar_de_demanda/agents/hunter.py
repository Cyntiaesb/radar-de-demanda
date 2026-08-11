"""🎯 Agente Hunter — caça quem JÁ TÁ VENDENDO no nicho (reverse engineer).

Fonte primária: Mercado Livre (resultados ordenados por relevância/vendas).
Fonte secundária (fase 2): Hotmart catálogo público (em construção).

Output: top 5-10 produtos com ticket, formato, gancho extraído da headline.
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

from ..fontes.mercado_livre import buscar_produtos

PROMPT_HUNTER = """Você é Hunter do Radar de Demanda — caçador de top sellers no mercado BR.

Recebeu uma lista de produtos REAIS que estão vendendo no Mercado Livre BR pro nicho "{nicho}".

Sua tarefa: identificar os 5-10 produtos VENCEDORES e decompor a fórmula deles.

## PRODUTOS COLETADOS (Mercado Livre BR)

{produtos}

## OUTPUT (JSON puro)

```json
{{
  "top_vencedores": [
    {{
      "rank": 1,
      "titulo": "título exato do produto",
      "ticket": 297.0,
      "vendidos": 1200,
      "formato": "curso online|ebook|mentoria|software|produto físico|outro",
      "headline_extraida": "1 frase que captura o gancho de venda do título",
      "angulo": "qual o ângulo de posicionamento (autoridade, transformação, atalho, status, etc)",
      "url": "url do anúncio",
      "porque_vende": "1 linha — por que esse vende mais que os outros"
    }}
    // 5-10 itens, ordenados pelo número de vendidos (mais → menos)
  ],
  "fórmula_vencedora": {{
    "ticket_medio_top_10": 0.0,
    "ticket_min": 0.0,
    "ticket_max": 0.0,
    "formato_dominante": "qual formato mais aparece no top 10",
    "angulo_dominante": "qual ângulo mais aparece",
    "padroes_de_headline": ["3-5 padrões repetidos nas headlines"],
    "saturacao": "alta|media|baixa",
    "oportunidade_de_ataque": "1 parágrafo: onde o vencedor é fraco — qual ângulo NÃO foi atacado ainda"
  }}
}}
```

REGRAS:
- Use APENAS produtos da lista coletada — não invente
- Se um produto não tem `vendidos` informado, marque como null mas ainda inclua se relevante
- "porque_vende" é raciocínio, não dado bruto
- Português BR
- SOMENTE JSON"""


def hunter(nicho: str, seeds: list[str], *, model: str = "claude-haiku-4-5-20251001") -> dict:
    """Caça top sellers e decompõe a fórmula vencedora.

    Args:
        nicho: nome do nicho (pra contexto do prompt)
        seeds: queries pra buscar no ML (3-6 termos é o ideal)
    """
    print("\n🎯 [Hunter] Caçando top sellers no Mercado Livre BR...")
    # Queries comerciais: prefixa "curso", "treinamento" pra captar produto vendido
    queries_comerciais = []
    for s in seeds[:4]:
        queries_comerciais.append(s)
        queries_comerciais.append(f"curso {s}")
        queries_comerciais.append(f"treinamento {s}")
    produtos = buscar_produtos(queries_comerciais[:10], limit=15, delay=0.4)
    if not produtos:
        produtos = buscar_produtos([nicho], limit=20, delay=0.4)
    if not produtos:
        print("    ⚠ nenhum produto coletado — Hunter retorna fallback")
        return {
            "top_vencedores": [],
            "fórmula_vencedora": {
                "ticket_medio_top_10": None,
                "formato_dominante": "indefinido",
                "angulo_dominante": "indefinido",
                "saturacao": "baixa",  # fallback otimista — sem evidência de saturação
                "oportunidade_de_ataque": "Mercado Livre não retornou produtos vendendo nesse termo — possível indício de mercado pouco explorado ou termo de pesquisa não-comercial. Reforce o termo com palavra-chave de produto (ex: 'curso X', 'mentoria Y').",
                "padroes_de_headline": [],
            },
        }

    produtos_str = "\n".join(
        f"- '{p['texto']}' | R${p['metadata'].get('preco', '?')} | "
        f"vendidos: {p['metadata'].get('vendidos', '?')} | {p['url']}"
        for p in produtos[:50]
    )

    prompt = PROMPT_HUNTER.format(nicho=nicho, produtos=produtos_str)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(model=model, max_tokens=3000, messages=[{"role": "user", "content": prompt}])
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()

    out = json.loads(raw)
    print(f"    ✓ {len(out.get('top_vencedores', []))} vencedores decodificados")
    print(f"    ✓ ticket médio: R${out.get('fórmula_vencedora', {}).get('ticket_medio_top_10', '?')}")
    return out
