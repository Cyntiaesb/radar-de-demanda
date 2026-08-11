"""🛒 Agente InfoHunter — caça top infoprodutos Hotmart e decodifica fórmula vencedora.

Complementa o Hunter (que usa Mercado Livre).
InfoHunter é OBRIGATÓRIO pra mercado de infoproduto/curso/mentoria.

Output: top 10 produtos Hotmart + fórmula (ticket médio, formato, ângulos)
        + URLs prontas pro cliente abrir manualmente (sempre).
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

from ..fontes.hotmart import buscar_infoprodutos, build_search_url

PROMPT_INFOHUNTER = """Você é InfoHunter do Cookia — analista de mercado de infoproduto BR.

Você recebeu produtos REAIS vendendo na Hotmart pro nicho "{nicho}".

Hotmart = onde o jogo do infoproduto acontece no Brasil. Se um curso tá lá com rating + vendas, é referência de mercado.

## INFOPRODUTOS COLETADOS

{produtos_block}

## SUA TAREFA

Identifique os 5-10 vencedores e decompõe a fórmula:

```json
{{
  "top_vencedores_hotmart": [
    {{
      "rank": 1,
      "titulo": "título exato",
      "ticket": 297.0,
      "rating": 4.8,
      "formato": "curso online | mentoria | comunidade | ebook | método",
      "headline_extraida": "1 frase que captura o gancho de venda do título",
      "angulo": "transformação | autoridade | atalho | medo | curiosidade | prova social | status",
      "url": "url do produto",
      "porque_vende": "1 linha — por que vende mais que os outros do nicho"
    }}
    // 5-10 itens
  ],
  "formula_vencedora_hotmart": {{
    "ticket_medio_top_10": 0.0,
    "ticket_min": 0.0,
    "ticket_max": 0.0,
    "formato_dominante": "qual formato mais aparece",
    "angulo_dominante": "qual ângulo mais aparece nos títulos",
    "padroes_de_headline": ["3-5 padrões repetidos"],
    "saturacao": "alta | media | baixa",
    "ticket_sweet_spot": "faixa onde o mercado paga mais (ex: 'R$297-497')",
    "oportunidade_de_ataque": "1 parágrafo: qual ângulo NÃO foi atacado ainda no nicho"
  }}
}}
```

REGRAS:
- Use SOMENTE produtos da lista coletada
- Se rating não vier, marque como null mas inclua o produto
- Português BR
- SOMENTE JSON, sem markdown"""


def info_hunter(nicho: str, seeds: list[str], *, model: str = "claude-haiku-4-5-20251001") -> dict:
    """Caça top infoprodutos Hotmart + analisa fórmula vencedora."""
    print("\n🛒 [InfoHunter] Caçando top infoprodutos Hotmart BR...")

    raw = buscar_infoprodutos(seeds[:6], limit=15, delay=0.8)

    resultado: dict = {
        "scraping_funcionou": raw["scraping_funcionou"],
        "urls_busca": raw["urls_busca"],
    }

    if not raw["scraping_funcionou"] or not raw["produtos"]:
        print(f"    ⚠ Hotmart bloqueou — entregando {len(raw['urls_busca'])} URLs prontas pra cliente abrir manualmente")
        resultado["top_vencedores_hotmart"] = []
        resultado["formula_vencedora_hotmart"] = {
            "ticket_medio_top_10": None,
            "formato_dominante": "indefinido",
            "saturacao": "indefinida",
            "oportunidade_de_ataque": "Hotmart bloqueou scraping. Abra os links manualmente — produtos top do nicho aparecem ordenados por relevância na busca da Hotmart.",
            "padroes_de_headline": [],
        }
        return resultado

    print(f"    ✓ {len(raw['produtos'])} infoprodutos capturados — analisando com Sonnet")

    produtos_str = "\n".join(
        f"- '{p['texto']}' | R${p['metadata'].get('preco', '?')} | "
        f"rating: {p['metadata'].get('rating', '?')} | "
        f"vendido: {p['metadata'].get('vendido', '?')} | {p['url']}"
        for p in raw["produtos"][:50]
    )

    prompt = PROMPT_INFOHUNTER.format(nicho=nicho, produtos_block=produtos_str)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(model=model, max_tokens=3500, messages=[{"role": "user", "content": prompt}])
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()

    analise = json.loads(text)
    resultado.update(analise)
    print(f"    ✓ {len(analise.get('top_vencedores_hotmart', []))} vencedores decodificados")
    print(f"    ✓ ticket médio top: R${analise.get('formula_vencedora_hotmart', {}).get('ticket_medio_top_10', '?')}")
    return resultado
