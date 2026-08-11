# Radar de Demanda

**Pesquisa de demanda brasileira via Claude** — descobre o que seu mercado-alvo realmente busca, reclama e desabafa, direto do Google Autocomplete BR, Reddit BR e Reclame Aqui, e gera um dossiê ranqueado por dor real (não achismo).

- **Grátis e open-source.** Roda como Claude Code Skill — você usa sua própria chave Anthropic (BYO key), sem servidor, sem assinatura.
- **Fontes de dor/intenção:** Google Autocomplete BR + Reddit BR + Reclame Aqui + comentários de YouTube.
- **Fontes de compra real:** Mercado Livre (produto vendendo) + Hotmart/Kiwify/Braip/Monetizze/Eduzz (infoproduto — só Hotmart tem busca pública, as outras 4 exigem login de afiliado e entram como link pronto) + Meta Ads Library (anúncio rodando agora).
- **4 skills incluídas:** `radar` (pesquisa + dossiê), `radar-copy` (copy de conversão a partir do dossiê), `radar-ads` (criativos de anúncio a partir do dossiê), `radar-expand` (mais variações sem raspar de novo).

## Quick start

Veja [INSTALL.md](INSTALL.md) pro passo a passo completo (~10 min a primeira vez).

```bash
# 1. Setar key
export ANTHROPIC_API_KEY=sk-ant-...

# 2. Rodar pra um nicho qualquer
python scripts/radar_run.py "advocacia tributária"

# 3. Ver output
cat data/dossies/<nicho>_<data>.md
```

## Estrutura

```
.claude/skills/radar/        # SKILL.md que o Claude Code carrega (+ radar-ads, radar-copy, radar-expand)
radar_de_demanda/            # Módulo Python standalone
├── fontes/                   # Scrapers (Google, Reddit, RA, YouTube...)
├── agents/                   # Agentes de pesquisa/categorização/expansão
└── smf_generator.py          # Solution-Market Fit
scripts/                      # CLIs amigáveis
data/dossies/                 # Output do usuário (não versionado)
```

## Custo por dossiê

| Etapa | Custo |
|---|---|
| Coleta (Google + Reddit + Reclame Aqui) | Grátis |
| Categorização (Claude Haiku) | ~R$3 |
| Solution-Market Fit (opcional, Sonnet) | ~R$8 |
| **Total típico** | **R$3–R$11** |

## Suporte

Dúvida ou bug: abra uma Issue aqui no repo, ou me chama no Instagram [@cyntiaesberard](https://instagram.com/cyntiaesberard).
