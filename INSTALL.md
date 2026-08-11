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
- Vá em **Billing** → adicione US$5 de crédito (dá pra ~25 dossiês)

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

### 3. Aguardar ~3-5 minutos

O Claude vai:
1. Raspar Google + Reddit + Reclame Aqui (5 min)
2. Categorizar com Haiku (1 min)
3. Gerar dossiê em `data/dossies/advocacia_<data>.md`

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

**Dossiê veio vazio ou raso**
→ Tente um nicho mais específico ("advocacia trabalhista" em vez de "direito").

---

## Custos por dossiê

| Etapa | Custo |
|---|---|
| Coleta (Google + Reddit + RA) | Grátis |
| Categorização Haiku | ~R$3 |
| Solution-Market Fit (opcional, Sonnet) | ~R$8 |
| **Total típico** | **R$3–R$11** |

US$5 de crédito = ~25 dossiês.

---

## Suporte

Dúvida ou bug: abra uma Issue neste repositório, ou me chama no Instagram [@cyntiaesberard](https://instagram.com/cyntiaesberard).
