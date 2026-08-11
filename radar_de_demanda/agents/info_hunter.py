"""🛒 Agente InfoHunter — caça top infoprodutos em 5 plataformas BR e decodifica fórmula vencedora.

Complementa o Hunter (que usa Mercado Livre).
InfoHunter é OBRIGATÓRIO pra mercado de infoproduto/curso/mentoria.

Fontes: Hotmart (busca pública, scraping real) + Kiwify, Braip, Monetizze,
Eduzz (marketplaces exigem login de afiliado — sem endpoint público, então
essas 4 sempre entram como link pronto pro cliente abrir manualmente logado).

Output: top 10 produtos (com plataforma de origem) + fórmula (ticket médio,
        formato, ângulos) + URLs prontas pro cliente abrir manualmente (sempre,
        nas 5 plataformas).
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

from ..fontes.hotmart import buscar_infoprodutos as _buscar_hotmart
from ..fontes.kiwify import buscar_infoprodutos as _buscar_kiwify
from ..fontes.braip import buscar_infoprodutos as _buscar_braip
from ..fontes.monetizze import buscar_infoprodutos as _buscar_monetizze
from ..fontes.eduzz import buscar_infoprodutos as _buscar_eduzz

FONTES_INFOPRODUTO = [
    ("hotmart", _buscar_hotmart),
    ("kiwify", _buscar_kiwify),
    ("braip", _buscar_braip),
    ("monetizze", _buscar_monetizze),
    ("eduzz", _buscar_eduzz),
]

PROMPT_INFOHUNTER = """Você é InfoHunter do Radar de Demanda — analista de mercado de infoproduto BR.

Você recebeu produtos REAIS vendendo em marketplaces de infoproduto BR (Hotmart, e possivelmente Kiwify/Braip/Monetizze/Eduzz) pro nicho "{nicho}".

Cada produto tem a plataforma de origem marcada. Se um curso tá lá com rating + vendas, é referência de mercado.

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
      "plataforma": "hotmart | kiwify | braip | monetizze | eduzz",
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
    """Caça top infoprodutos nas 5 plataformas BR + analisa fórmula vencedora.

    Só Hotmart tem busca pública (scraping real). Kiwify/Braip/Monetizze/Eduzz
    exigem login de afiliado — sempre entram como link pronto, sem produtos.
    """
    print("\n🛒 [InfoHunter] Caçando top infoprodutos em 5 plataformas BR...")

    produtos: list[dict] = []
    urls_busca: list[dict] = []
    algum_funcionou = False

    for nome_fonte, buscar_fn in FONTES_INFOPRODUTO:
        raw = buscar_fn(seeds[:6], limit=15, delay=0.8)
        for u in raw["urls_busca"]:
            urls_busca.append({**u, "plataforma": nome_fonte})
        if raw["scraping_funcionou"] and raw["produtos"]:
            algum_funcionou = True
            for p in raw["produtos"]:
                p.setdefault("metadata", {})["plataforma"] = nome_fonte
                produtos.append(p)
            print(f"    ✓ {nome_fonte}: {len(raw['produtos'])} infoprodutos capturados")
        else:
            print(f"    ⚠ {nome_fonte}: sem scraping (login exigido ou bloqueio) — link manual entregue")

    resultado: dict = {
        "scraping_funcionou": algum_funcionou,
        "urls_busca": urls_busca,
    }

    if not algum_funcionou or not produtos:
        print(f"    ⚠ Nenhuma fonte com scraping ativo — entregando {len(urls_busca)} URLs prontas pra cliente abrir manualmente")
        resultado["top_vencedores_hotmart"] = []
        resultado["formula_vencedora_hotmart"] = {
            "ticket_medio_top_10": None,
            "formato_dominante": "indefinido",
            "saturacao": "indefinida",
            "oportunidade_de_ataque": "Nenhuma plataforma retornou produtos via scraping (Hotmart bloqueou, ou as demais exigem login). Abra os links manualmente — produtos top do nicho aparecem ordenados por relevância em cada marketplace.",
            "padroes_de_headline": [],
        }
        return resultado

    print(f"    ✓ {len(produtos)} infoprodutos no total — analisando com Sonnet")

    produtos_str = "\n".join(
        f"- '{p['texto']}' | R${p['metadata'].get('preco', '?')} | "
        f"rating: {p['metadata'].get('rating', '?')} | "
        f"vendido: {p['metadata'].get('vendido', '?')} | "
        f"plataforma: {p['metadata'].get('plataforma', '?')} | {p['url']}"
        for p in produtos[:50]
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
