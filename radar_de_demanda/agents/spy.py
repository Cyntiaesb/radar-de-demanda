"""🕵️ Agente Spy — espia a Meta Ads Library e decodifica ângulos vencedores.

Por que isso é o killer feature: anúncio rodando há +30 dias é OFERTA VALIDADA
com dinheiro real sendo gasto. Não é hipótese — é prova.

Fluxo:
  1. Recebe nicho + vocabulário (do Analyst)
  2. Monta keywords ótimas pra Meta Ads Library
  3. Tenta scraping (graceful: se falhar, ainda gera URLs prontas)
  4. Sonnet analisa textos extraídos → extrai ângulos, hooks, formatos
  5. Retorna top anúncios + URLs + análise estratégica
"""
from __future__ import annotations
import json
import os

from anthropic import Anthropic

from ..fontes.meta_ads_library import build_search_url, espiona_nicho
from ..fontes import apify_fontes as apify

PROMPT_SPY = """Você é Spy do Radar de Demanda — analista de anúncios pagos da Meta Ads Library BR.

Você recebeu textos REAIS de anúncios rodando no Facebook/Instagram BR pro nicho "{nicho}".

**REGRA DE OURO:** anúncio com `dias_rodando >= 60` é **oferta validada com R$** — paga ela mesma.
Anúncio com `dias_rodando >= 120` é **OFERTA-MÃE do nicho** — referência principal.
Anúncio rodando < 30 dias = teste ainda, peso menor.

Ranqueie e analise considerando dias rodando como principal sinal de profitabilidade.

## ANÚNCIOS COLETADOS (ordenados do mais antigo pro mais novo)

{anuncios_block}

## SUA TAREFA

Analise os anúncios e gere:

1. **Top 5-10 anúncios mais promissores** — os que sinalizam maior tração
2. **Padrões de ângulo dominantes** — qual posicionamento mais aparece
3. **Hooks vencedores extraídos** — as primeiras frases que mais se repetem
4. **Gap de mercado** — qual ângulo NÃO foi ainda explorado (onde atacar)

## OUTPUT (JSON puro)

```json
{{
  "top_anuncios": [
    {{
      "rank": 1,
      "pagina": "nome da página/marca anunciante",
      "dias_rodando": 142,
      "validacao": "oferta-mãe (>120d) | validada (>60d) | em teste (<30d)",
      "texto_resumido": "1 frase capturando a essência do anúncio",
      "angulo": "qual posicionamento (transformação | autoridade | atalho | medo | curiosidade | prova social | etc)",
      "hook": "primeira frase ou gancho extraído",
      "formato_implicito": "ebook | curso | mentoria | consultoria | produto físico | aplicativo | serviço",
      "porque_funciona": "1 linha — por que esse ângulo converte nesse público"
    }}
    // 5-10 itens
  ],
  "padroes_dominantes": {{
    "angulo_top_1": "qual é o ângulo mais usado nos anúncios",
    "angulo_top_2": "qual é o segundo mais usado",
    "formato_dominante": "qual formato de oferta predomina",
    "padroes_de_hook": ["3-5 padrões de abertura repetidos"]
  }},
  "gap_de_mercado": {{
    "angulo_inexplorado": "qual posicionamento NINGUÉM tá atacando ainda",
    "porque_oportunidade": "1 parágrafo — por que cliente que entrar por esse ângulo ganha",
    "hook_sugerido": "1 hook pronto pra cliente testar com esse gap"
  }}
}}
```

REGRAS:
- Use apenas dados dos anúncios coletados — não invente
- Português BR
- SOMENTE JSON, sem markdown ao redor"""


def spy(
    nicho: str,
    seeds: list[str],
    vocabulario: list[str] | None = None,
    *,
    model: str = "claude-haiku-4-5-20251001",
) -> dict:
    """Espia Meta Ads Library e analisa ângulos vencedores.

    Args:
        nicho: nicho-alvo
        seeds: queries seed do mercado
        vocabulario: opcional, termos crus do Analyst (afina busca)

    Returns:
        {
          "scraping_funcionou": bool,
          "urls_busca": [{"keyword", "url"}],  # sempre preenchido
          "top_anuncios": [...] (se scraping funcionou),
          "padroes_dominantes": {...},
          "gap_de_mercado": {...}
        }
    """
    print("\n🕵️  [Spy] Espionando Meta Ads Library BR...")

    keywords = list(seeds[:5])
    if vocabulario:
        keywords.extend([v for v in vocabulario[:3] if len(v) > 3 and len(v) < 50])

    raw = None
    if apify.token():
        try:
            ads = apify.meta_anuncios(keywords)
            raw = {
                "anuncios_extraidos": ads,
                "urls_busca": [{"keyword": k, "url": build_search_url(k)} for k in keywords],
                "scraping_funcionou": bool(ads),
            }
            print(f"    💵 Apify (Meta): US$ {apify.GASTOS.get('meta_ads', 0)}")
        except Exception as e:  # cai no caminho direto + links
            print(f"    ⚠ Apify (Meta) falhou: {type(e).__name__}: {str(e)[:120]}")
    if raw is None:
        raw = espiona_nicho(keywords, max_total=30, delay=1.0)

    resultado = {
        "scraping_funcionou": raw["scraping_funcionou"],
        "urls_busca": raw["urls_busca"],
        "anuncios_brutos": raw["anuncios_extraidos"],
    }

    if not raw["scraping_funcionou"] or not raw["anuncios_extraidos"]:
        print(f"    ⚠ Meta bloqueou ou retornou JS-only — gerando {len(raw['urls_busca'])} URLs prontas pra cliente abrir manualmente")
        resultado["top_anuncios"] = []
        resultado["padroes_dominantes"] = {"observacao": "scraping bloqueado — abra URLs manualmente"}
        resultado["gap_de_mercado"] = {"observacao": "análise manual recomendada"}
        return resultado

    # Rankeia por dias rodando (mais antigo = oferta mais validada)
    anuncios_ranqueados = sorted(
        raw["anuncios_extraidos"],
        key=lambda a: (a.get("dias_rodando") or 0),
        reverse=True,
    )
    validados = sum(1 for a in anuncios_ranqueados if (a.get("dias_rodando") or 0) >= 60)
    print(f"    ✓ {len(anuncios_ranqueados)} anúncios capturados ({validados} rodando há +60d = oferta validada)")

    anuncios_block = "\n\n".join(
        f"### Anúncio {i+1} (página: {a.get('pagina', '?')} | dias rodando: {a.get('dias_rodando') or '?'})\n{a.get('texto', '')[:400]}"
        for i, a in enumerate(anuncios_ranqueados[:25])
    )
    resultado["anuncios_brutos"] = anuncios_ranqueados

    prompt = PROMPT_SPY.format(nicho=nicho, anuncios_block=anuncios_block)

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

    print(f"    ✓ {len(analise.get('top_anuncios', []))} ângulos decodificados")
    return resultado
