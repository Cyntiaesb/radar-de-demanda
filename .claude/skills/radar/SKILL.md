---
name: radar
description: Pesquisa de demanda brasileira via Claude. Coleta sinais reais de dor (Google Autocomplete BR + Reddit BR + Reclame Aqui + YouTube) e de compra efetiva (Mercado Livre + Hotmart/Kiwify/Braip/Monetizze/Eduzz + Meta Ads Library) por nicho, ranqueia as dores com Claude e gera dossiê PT-BR com personas, top vencedores, vocabulário real do público e ofertas. Fonte bloqueada vira link de busca para abrir à mão. Use quando o usuário pedir pesquisa de mercado, análise de dor, validação de oferta ou briefs de conteúdo SEO em qualquer nicho B2B/B2C brasileiro.
---

# /radar — Pesquisa de Demanda Brasileira

## Quando invocar

- "Quero entender o mercado de <nicho>"
- "Gera dossiê demand intel pra <nicho>"
- "O que as pessoas buscam quando procuram <serviço>?"
- "Cria uma oferta pra esse lead/cliente"

## Passo a passo (nesta ordem)

1. **Confira se existe `data/brief.json`.** Se não existir, pare e peça para a pessoa rodar o briefing
   **no terminal dela** (ele faz perguntas e precisa de alguém digitando):

   ```bash
   python scripts/radar_brief.py
   ```

   Não rode o briefing pelo Claude Code: ele espera respostas no teclado.

2. **Rode o dossiê sempre com `--sem-pausa`** (dentro do Claude Code ninguém responde perguntas no meio):

   ```bash
   python scripts/radar_run.py "<nicho>" --sem-pausa
   ```

   A rodada leva vários minutos: use timeout longo (até 10 min) ou rode em segundo plano.
   Só acrescente `--landing` se a pessoa pedir a landing de 9 seções (custa 1 chamada a mais ao Sonnet).

3. **Se o programa parar com "Só N frase(s) real(is) coletada(s)"**, repasse a mensagem como veio:
   a coleta não trouxe dado suficiente e o Radar parou antes de gastar com o modelo. Não invente dossiê.

## O que a pessoa recebe

Em `data/dossies/<nicho>_<data>`:

- `.md` (para ler), `.html` (painel no navegador), `.csv` (ofertas) e `.json` (usado por `/radar-copy` e `/radar-ads`)
- Dores ranqueadas por Pain Score, personas, vocabulário real do público, ofertas com score
- Seção **"Fontes indisponíveis hoje — abra à mão"** com links de busca das fontes que bloquearam a coleta

## Custo

O custo depende do modelo e do tamanho da coleta. Uma rodada faz 2 chamadas ao Claude Sonnet
(Analyst e Strategist) e de 1 a 4 ao Claude Haiku (Router sempre; Hunter, InfoHunter e Spy só quando
a fonte deles traz dado). Com `--landing`, mais 1 ao Sonnet. O briefing faz 1 chamada ao Haiku.
Confira o gasto real no painel da Anthropic (console.anthropic.com, em Usage).

## Setup da pessoa (primeira vez)

1. Instalar dependências: `pip install -r requirements.txt`
2. Colocar `ANTHROPIC_API_KEY` no `.env`
3. Rodar o briefing no terminal: `python scripts/radar_brief.py`
4. Pedir no Claude Code: `/radar seu primeiro nicho`

## Anti-patterns

- Não rodar pro mesmo nicho < 30d (sinais mudam pouco)
- Não usar % inventado nos hooks (Radar de Demanda gera linguagem de processo, não promessa numérica)
- Não comparar concorrentes nominalmente em copy pra setores regulados (OAB, CFM, CFN)
- Não tentar contornar bloqueio de site: fonte bloqueada entra como link para abrir à mão
