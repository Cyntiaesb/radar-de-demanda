# Radar de Demanda

**Pesquisa de demanda brasileira via Claude** — descobre o que seu mercado-alvo realmente busca, reclama e desabafa e gera um dossiê ranqueado por dor real (não achismo).

- **Grátis e open-source.** Roda como Claude Code Skill — você usa sua própria chave Anthropic (BYO key), sem servidor, sem assinatura.
- **Fontes de dor/intenção:** Google Autocomplete BR + Reddit BR + Reclame Aqui + comentários de YouTube.
- **Fontes de compra real:** Mercado Livre (produto vendendo) + Hotmart/Kiwify/Braip/Monetizze/Eduzz (infoproduto — só Hotmart tem busca pública, as outras 4 exigem login de afiliado e entram como link pronto) + Meta Ads Library (anúncio rodando agora).
- **Fonte bloqueada vira link.** Vários sites bloqueiam coleta automática (anti-robô, login, limite de pedidos). O Radar não tenta contornar: registra "fonte indisponível hoje" e o dossiê traz os links de busca para você abrir à mão.
- **Sem dado, sem dossiê.** Se a coleta trouxer menos de 10 frases reais, o Radar para antes de chamar qualquer modelo pago e diz quais fontes falharam.
- **4 skills incluídas:** `radar` (pesquisa + dossiê), `radar-copy` (copy de conversão a partir do dossiê), `radar-ads` (criativos de anúncio a partir do dossiê), `radar-expand` (mais variações sem coletar de novo).

## Quick start

Veja [INSTALL.md](INSTALL.md) pro passo a passo completo (~10 min a primeira vez).

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Colocar a chave: renomeie .env.example para .env e cole sua ANTHROPIC_API_KEY

# 3. Responder o briefing (uma vez, no terminal — ele faz perguntas)
python scripts/radar_brief.py

# 4. Rodar pra um nicho
python scripts/radar_run.py "advocacia tributária"
#    dentro do Claude Code: /radar advocacia tributária  (a skill usa --sem-pausa)

# 5. Ver o resultado
#    data/dossies/<nicho>_<data>.md  (e .html, .csv, .json)
```

Opções do `radar_run.py`:

- `--sem-pausa` — não faz perguntas no meio da rodada. Ligado sozinho quando o terminal não é interativo (como no Claude Code).
- `--landing` — gera também a landing de 9 seções (1 chamada a mais ao Sonnet). Desligado por padrão.

## Estrutura

```
.claude/skills/radar/        # SKILL.md que o Claude Code carrega (+ radar-ads, radar-copy, radar-expand)
radar_de_demanda/            # Módulo Python standalone
├── fontes/                   # Coletores (Google, Reddit, RA, YouTube...) + links_manuais.py
├── agents/                   # Agentes de pesquisa/categorização/expansão
└── smf_generator.py          # Solution-Market Fit
scripts/                      # CLIs (radar_brief.py, radar_run.py, radar_expand.py...)
tests/                        # Testes sem rede: python -m unittest discover -s tests
data/                         # brief.json e dossies/ (não versionado)
```

## Custo por dossiê

O custo depende do modelo e do tamanho da coleta, e é cobrado na sua chave da Anthropic:

| Etapa | Chamadas ao modelo |
|---|---|
| Briefing (uma vez) | 1 ao Claude Haiku |
| Coleta (Google, Reddit, Reclame Aqui, Mercado Livre, Trends, YouTube) | nenhuma (grátis) |
| Dossiê | 2 ao Claude Sonnet (Analyst e Strategist) + 1 a 4 ao Claude Haiku (Router sempre; Hunter, InfoHunter e Spy só quando a fonte deles traz dado) |
| Landing (`--landing`, opcional) | +1 ao Claude Sonnet |
| Cada expansão (`radar_expand.py`) | 1 ao Claude Sonnet |

Confira o gasto real no painel da Anthropic (console.anthropic.com, em Usage).

## Testes

```bash
python -m unittest discover -s tests
```

## Suporte

Dúvida ou bug: abra uma Issue aqui no repo, ou me chama no Instagram [@cyntiaesberard](https://instagram.com/cyntiaesberard).
