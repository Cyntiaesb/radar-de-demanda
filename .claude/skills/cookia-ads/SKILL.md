---
name: cookia-ads
description: Gera criativos de anúncio pago (Meta, Google Search, Google PMax, YouTube, TikTok, LinkedIn) consumindo um dossiê do Cookia. Cada anúncio é estruturado por estágio de consciência do público (Schwartz) e respeita limite de caracteres e política de cada plataforma. Use quando o usuário pedir criativo de anúncio, copy de mídia paga, roteiro de Reels/TikTok pra ads, ou estratégia de campanha derivada de um dossiê Cookia.
---

# /cookia-ads — Criativos de Mídia Paga Dossiê-Driven

## Pré-requisito

Existir um dossiê em `data/dossies/<nicho>_<data>.md`. Se não existir, perguntar o nicho e rodar `cookia` antes.

## Quando invocar

- "Cria anúncio Meta pra esse nicho"
- "Headline de Google Ads"
- "Roteiro de TikTok ad 30s"
- "Asset group de PMax"
- "Hook de YouTube pre-roll"

## Catálogo de prompts (25 peças, 5 plataformas)

### Meta Ads — Facebook/Instagram (10)
1. `meta-primary-unaware` — Primary text estágio unaware
2. `meta-primary-problem` — Primary text problem-aware
3. `meta-primary-solution` — Primary text solution-aware
4. `meta-primary-most` — Primary text most-aware
5. `meta-headline-5` — 5 headlines (40 char)
6. `meta-descricao` — Descrição link
7. `meta-reels-15s` — Roteiro Reels ad 15s
8. `meta-reels-30s` — Roteiro Reels ad 30s
9. `meta-estatico` — Criativo estático (briefing imagem + texto)
10. `meta-carrossel-5` — Carrossel 5 slides

### Google Ads — Search + PMax (6)
11. `google-titulos-15` — 15 títulos responsivos (30 char)
12. `google-descricoes-4` — 4 descrições responsivas (90 char)
13. `google-sitelink` — Extensão sitelink (consome `duvidas_frequentes`)
14. `google-frase-destaque` — Extensão frase de destaque
15. `google-display` — Anúncio display (headline + descrição curta)
16. `google-pmax-asset` — Asset group PMax completo

### YouTube Ads (4)
17. `yt-bumper-6s` — Bumper non-skippable
18. `yt-preroll-15s` — Pre-roll skippable
19. `yt-preroll-30s` — Pre-roll skippable
20. `yt-instream-60s` — In-stream completo

### TikTok Ads (3)
21. `tt-hook-3s` — Hook primeiro frame
22. `tt-spark-ugc-30s` — Spark Ads UGC script
23. `tt-topview-60s` — TopView script

### LinkedIn Ads (2) — só B2B
24. `li-sponsored` — Sponsored content text
25. `li-message-ad` — Message Ad / InMail patrocinado

## Como usar

```
/cookia-ads <id-do-prompt> [caminho-do-dossiê]
```

Exemplos:
- `/cookia-ads meta-primary-problem` → usa dossiê mais recente
- `/cookia-ads google-titulos-15 advocacia`
- `/cookia-ads tt-hook-3s data/dossies/contabilidade_2026-05-15.md`

## Output padrão

Toda peça vem com:
1. **Variações** dentro do limite de char da plataforma
2. **Estágio de consciência alvo** (Schwartz)
3. **Conformidade** — flag de risco com política da plataforma (ex: claim de saúde, financeiro)
4. **Campos do dossiê consumidos**

## Anti-patterns

- Não passar de limite de caracteres (Meta primary: 125 recomendado, headline: 40, descrição: 30)
- Não usar claim médico/financeiro sem disclaimer em nicho regulado
- Não rodar campanha unaware com criativo most-aware (mismatch = CPA explode)
- Não copiar concorrente nominalmente em setor com OAB/CFM/CFN
