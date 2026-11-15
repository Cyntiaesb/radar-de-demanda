# Instalar Radar de Demanda — Passo a Passo (Claude Code Desktop)

Tempo total: **~10 minutos** na primeira vez. Depois, cada dossiê leva 30s pra começar.

---

## Pré-requisitos (uma vez na vida)

### 1. Baixar Claude Code Desktop

- Acesse: https://claude.com/claude-code
- Baixe a versão pro seu sistema (Windows ou Mac)
- Instale como qualquer programa (next, next, finish)

### 2. Criar conta Anthropic + API Key

- Acesse: https://console.anthropic.com
- Crie conta com seu email
- Vá em **API Keys** → **Create Key** → copie a chave (começa com `sk-ant-...`)
- Vá em **Billing** → adicione crédito (o gasto de cada dossiê aparece em **Usage**)

> ⚠️ **Guarde a chave em local seguro.** Você não vê ela de novo depois de fechar a janela.

### 3. Instalar Python 3.11+

- **Windows:** baixe em https://python.org/downloads (marque "Add Python to PATH")
- **Mac:** já vem instalado (`python3 --version` no Terminal pra confirmar)

---

## Instalar o Radar de Demanda (uma vez)

### 1. Baixar o repositório

Clone ou baixe o `.zip` deste repositório numa pasta que você lembre. Recomendo:

- **Windows:** `C:\Users\SeuNome\Documents\RADAR DE DEMANDA\`
- **Mac:** `~/Documents/RADAR DE DEMANDA/`

### 2. Configurar a API key

Dentro da pasta RADAR DE DEMANDA, encontre o arquivo `.env.example`. Renomeie pra `.env` e abra no bloco de notas. Cole sua chave:

```
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
```

Salve e feche.

**Opcional: as outras fontes pelo Apify.** Sem isso, o Radar traz só o Google Autocomplete e entrega links prontos para Reddit, Reclame Aqui, Mercado Livre, Google Trends e anúncios da Meta, porque esses sites bloqueiam coleta direta. Para o Radar buscar nesses sites sozinho:

1. Crie uma conta em https://console.apify.com/sign-up (o plano grátis vem com um crédito por mês).
2. Copie o seu token em console.apify.com → Settings → API & Integrations.
3. No mesmo `.env`, acrescente:

```
APIFY_TOKEN=apify_api_seu-token-aqui
APIFY_TETO_USD=1.00
```

`APIFY_TETO_USD` é o máximo que uma rodada pode gastar no Apify, somando as 5 fontes. O gasto real aparece no fim da rodada e no dossiê.

### 3. Instalar dependências

Abra o terminal **dentro da pasta RADAR DE DEMANDA**:

- **Windows:** clique com botão direito na pasta segurando Shift → "Abrir terminal aqui"
- **Mac:** abra Terminal e digite `cd ~/Documents/RADAR DE DEMANDA`

Rode:

```
pip install -r requirements.txt
```

Espera ~1 minuto.

### 4. Copiar as skills pro Claude Code

A pasta `.claude/skills/` do Radar de Demanda precisa ser visível pro Claude Code Desktop. Mais fácil:

**Abra a pasta RADAR DE DEMANDA dentro do Claude Code Desktop** (File → Open Folder). Pronto — ele lê automaticamente as skills da pasta `.claude/skills/`.

### 5. Responder o briefing (uma vez, no terminal)

Ainda no terminal, dentro da pasta RADAR DE DEMANDA, rode:

```
python scripts/radar_brief.py
```

Responda às perguntas sobre o seu negócio e o seu nicho. É isso que define o que o Radar vai pesquisar. As respostas ficam em `data/brief.json`.

Rode no terminal, não no chat do Claude Code: o briefing espera você digitar as respostas. Sem esse passo, o dossiê para com "Brief não encontrado".

---

## Primeiro dossiê (toda vez)

### 1. Abrir o Claude Code Desktop na pasta RADAR DE DEMANDA

Se já abriu, ok. Senão: File → Open Folder → escolha RADAR DE DEMANDA.

### 2. Digitar o comando

Na caixa de chat, digite:

```
/radar advocacia
```

(Troque "advocacia" pelo seu nicho.)

### 3. Aguardar alguns minutos

O Claude roda `python scripts/radar_run.py "advocacia" --sem-pausa` e:
1. Coleta sinais no Google e, se você colocou o `APIFY_TOKEN`, também no Reddit, Reclame Aqui, Mercado Livre, Google Trends e anúncios da Meta
2. Ranqueia as dores e monta as ofertas com o Claude
3. Gera o dossiê em `data/dossies/advocacia_<data>.md` (e `.html`, `.csv`, `.json`)

Fonte que não trouxer dado aparece no dossiê como "indisponível hoje", com os links de busca para você abrir à mão. Se a coleta trouxer menos de 10 frases reais, o Radar para antes de gastar com o modelo e diz quais fontes falharam.

Quer também a landing de 9 seções? Peça ao Claude para rodar com `--landing` (1 chamada a mais ao Sonnet).

### 4. Abrir o dossiê

Tá tudo em **markdown** dentro de `data/dossies/`. Abra no próprio Claude Code (ele renderiza bonito) ou copie pro Notion/Docs.

---

## Usar os packs de copy e anúncios

Com o dossiê gerado, digite:

```
/radar-copy headline-landing
/radar-ads meta-primary-problem
```

O Claude pega automaticamente o dossiê mais recente e gera as variações.

**Catálogo completo de prompts:**
- Copy (30): veja `.claude/skills/radar-copy/SKILL.md`
- Ads (25): veja `.claude/skills/radar-ads/SKILL.md`

---

## Problemas comuns

**"Comando /radar não aparece"**
→ Você abriu a pasta RADAR DE DEMANDA dentro do Claude Code? File → Open Folder.

**"Erro: ANTHROPIC_API_KEY não encontrada"**
→ Confira se você renomeou `.env.example` pra `.env` (sem o `.example`).

**"pip não é reconhecido"**
→ Você instalou Python marcando "Add to PATH"? Reinstale marcando essa opção.

**"Erro 401 ou créditos insuficientes"**
→ Adicione crédito em console.anthropic.com → Billing.

**"Brief não encontrado"**
→ Faltou o passo 5 da instalação: rode `python scripts/radar_brief.py` no terminal.

**"Só N frase(s) real(is) coletada(s)"**
→ A coleta trouxe pouco dado e o Radar parou antes de gastar. Tente um nicho com mais busca, acrescente termos no briefing ou rode de novo mais tarde.

**Dossiê veio vazio ou raso**
→ Tente um nicho mais específico ("advocacia trabalhista" em vez de "direito").

---

## Custos por dossiê

O custo depende do modelo e do tamanho da coleta, e é cobrado na sua chave da Anthropic:

| Etapa | Chamadas ao modelo |
|---|---|
| Briefing (uma vez) | 1 ao Claude Haiku |
| Coleta | nenhuma (grátis) |
| Dossiê | 2 ao Claude Sonnet + 1 a 4 ao Claude Haiku |
| Landing (`--landing`, opcional) | +1 ao Claude Sonnet |

Confira o gasto real no painel da Anthropic (console.anthropic.com, em Usage).

---

## Suporte

Dúvida ou bug: abra uma Issue neste repositório, ou me chama no Instagram [@cyntiaesberard](https://instagram.com/cyntiaesberard).
