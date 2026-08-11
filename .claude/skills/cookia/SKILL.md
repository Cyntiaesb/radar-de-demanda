---
name: cookia
description: Pesquisa de demanda brasileira via Claude. Coleta sinais reais de busca (Google Autocomplete BR + Reddit BR + Reclame Aqui) por nicho, categoriza com Claude Haiku, e gera dossiê PT-BR ranqueado com sub-temas, vocabulário real do público, hooks de copy e ofertas únicas via Solution-Market Fit. Use quando o usuário pedir pesquisa de mercado, análise de dor, validação de oferta ou briefs de conteúdo SEO em qualquer nicho B2B/B2C brasileiro.
---

# /cookia — Pesquisa de Demanda Brasileira

## Quando invocar

- "Quero entender o mercado de <nicho>"
- "Gera dossiê demand intel pra <nicho>"
- "O que as pessoas buscam quando procuram <serviço>?"
- "Cria uma oferta pra esse lead/cliente"

## Comando principal

```bash
python scripts/cookia_run.py "<nicho>"
```

## O que o usuário recebe

Para cada nicho:

1. **Coleta** (5-10 min): Google Autocomplete BR + Reddit BR (+ Reclame Aqui em breve)
2. **Análise** (1-2 min): Claude Haiku agrupa sinais em 10-12 sub-temas
3. **Dossiê** (instant): `data/dossies/<nicho>_<data>.md` com:
   - Sub-temas ranqueados por volume
   - Vocabulário real do público
   - Hooks de copy sugeridos
   - Buscas representativas

4. **Solution-Market Fit** (opcional): pra um lead específico, gera oferta única outcome-based + battle cards.

## Custo médio por dossiê

- Coleta: free (Google + Reddit públicos)
- Análise Haiku: ~R$3
- SMF Sonnet (opcional): ~R$8 por lead

## Setup do usuário (primeira vez)

1. Instalar dependências: `pip install -r requirements.txt`
2. Setar `ANTHROPIC_API_KEY` no `.env`
3. Rodar `python scripts/cookia_run.py "seu primeiro nicho"`

## Anti-patterns

- Não rodar pro mesmo nicho < 30d (sinais mudam pouco)
- Não usar % inventado nos hooks (Cookia gera linguagem de processo, não promessa numérica)
- Não comparar concorrentes nominalmente em copy pra setores regulados (OAB, CFM, CFN)
