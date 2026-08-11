"""🧭 Agente Router — classifica o tipo de negócio e roteia pras fontes certas.

Roda ANTES do Scout. Custa ~R$0,30 (Haiku), economiza muito mais
em desperdício de scraping em fontes erradas.

Categorias:
  - curso_infoproduto   → Hotmart-style: cursos, mentorias, ebooks
  - produto_fisico      → e-commerce: Mercado Livre + Shopee
  - servico_b2b         → consultoria/agência: LinkedIn-style, RA empresarial
  - servico_b2c_local   → dentista, advogado, personal trainer
  - saas_software       → app, ferramenta digital

Output: RoutingConfig que o Scout consome.
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

PROMPT_ROUTER = """Você é Router do Radar de Demanda — classifica o tipo de negócio do CLIENTE FINAL pra escolher as fontes de pesquisa certas.

## CONTEXTO

Cliente é: "{negocio}"
Vende: "{o_que_vende}"
Pesquisa o nicho/mercado: "{nicho}"

## SUA TAREFA

Classifique em 1 das 5 categorias e gere a config de roteamento.

### Categorias

1. **curso_infoproduto** — cursos online, mentorias, ebooks, comunidades pagas (Hotmart-style)
2. **produto_fisico** — produtos vendidos em e-commerce (roupa, eletrônico, comida, etc)
3. **servico_b2b** — consultoria, agência, software pra empresa, serviço profissional B2B
4. **servico_b2c_local** — serviço pessoa-pra-pessoa (dentista, advogado, personal, esteticista)
5. **saas_software** — software/app/ferramenta digital (free ou paga)

### Queries comerciais reescritas

Pra cada categoria, reescreve o nicho em 5-8 termos de busca QUE GERAM SINAL DE COMPRA:

- curso_infoproduto: "curso X", "como aprender X", "mentoria X", "treinamento X"
- produto_fisico: "comprar X", "melhor X", "X preço", "X review"
- servico_b2b: "contratar X", "consultoria X", "agência X", "quanto custa X empresa"
- servico_b2c_local: "X perto de mim", "melhor X [cidade]", "vale a pena X", "X recomendação"
- saas_software: "melhor app X", "alternativa X", "X review", "como usar X"

## OUTPUT — JSON puro

```json
{{
  "categoria": "uma das 5 acima",
  "subcategoria": "1 frase mais específica (ex: 'curso de programação iniciante', 'consultoria de marketing pra advogados')",
  "racional": "1 linha — por que essa categoria",
  "fontes_ativas": {{
    "google_autocomplete": true,
    "reddit": true,
    "reclame_aqui": true,
    "google_trends": true,
    "mercado_livre": true
  }},
  "subreddits_recomendados": ["lista de 5-8 subreddits adequados"],
  "queries_comerciais": ["5-8 queries reescritas comercialmente"]
}}
```

### Regras de fontes_ativas

- `mercado_livre`: **true** pra `curso_infoproduto` e `produto_fisico`. **false** pra os outros (ML não tem serviço B2B nem SaaS).
- `reclame_aqui`: **true** sempre que faz sentido (dor com dinheiro envolvido). Pra SaaS, deixe true. Pra curso, true também.
- Os outros (Google, Reddit, Trends): sempre true.

### Subreddits recomendados por categoria

- **curso_infoproduto**: `empreendedorismo`, `marketingdigital`, `desabafos`, `conselhodecarreira`, `AskBrasil`, `freelaBR`
- **produto_fisico**: `empreendedorismo`, `AskBrasil`, `desabafos`, `PoupadosNet` (+ subs específicos do nicho se óbvio)
- **servico_b2b**: `empreendedorismo`, `vendas`, `marketingdigital`, `brdev`, `TIBrasil`, `freelaBR`
- **servico_b2c_local**: `desabafos`, `AskBrasil`, `conselhodecarreira`, `PoupadosNet`
- **saas_software**: `brdev`, `TIBrasil`, `marketingdigital`, `empreendedorismo`

Pode adicionar subs específicos do nicho se óbvio (ex: `direito` pra advocacia, `contabilidade` pra contabilidade).

Retorne SOMENTE o JSON, nada mais."""


def router(brief: dict, nicho: str, *, model: str = "claude-haiku-4-5-20251001") -> dict:
    """Classifica o negócio e gera config de roteamento.

    Args:
        brief: dict com 'negocio', 'o_que_vende'
        nicho: nicho/mercado a pesquisar

    Returns:
        dict com categoria, fontes_ativas, subreddits_recomendados, queries_comerciais
    """
    print("\n🧭 [Router] Classificando tipo de negócio...")

    prompt = PROMPT_ROUTER.format(
        negocio=brief.get("negocio", "?"),
        o_que_vende=brief.get("o_que_vende", "?"),
        nicho=nicho,
    )

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()

    config = json.loads(raw)
    print(f"    ✓ Categoria: {config.get('categoria')} ({config.get('subcategoria', '')})")
    fontes_ativas = [k for k, v in config.get("fontes_ativas", {}).items() if v]
    print(f"    ✓ Fontes ativas: {', '.join(fontes_ativas)}")
    print(f"    ✓ Subreddits: {len(config.get('subreddits_recomendados', []))} selecionados")
    print(f"    ✓ Queries comerciais: {len(config.get('queries_comerciais', []))} reescritas")
    return config
