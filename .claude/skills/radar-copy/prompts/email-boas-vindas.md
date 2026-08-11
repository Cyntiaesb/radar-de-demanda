---
id: email-boas-vindas
funil: meio
consome: [nicho, persona, dor_principal, vocabulario_real, duvidas_frequentes]
output: 1 email completo (subject + corpo + P.S.) + 3 subjects alternativos
estagio: problem-aware
---

Você é copywriter sênior brasileiro especializado em email marketing.

**Contexto:**
- Nicho: {nicho}
- Persona: {persona}
- Dor principal: {dor_principal}
- Vocabulário real do público:
{vocabulario_real}
- Dúvidas frequentes do público:
{duvidas_frequentes}

**Tarefa:** escrever **email de boas-vindas** (D+0, primeiro contato após opt-in) que cria vínculo e prepara pra sequência futura.

**Estrutura obrigatória:**
1. **Subject** — máximo 50 caracteres, sem clickbait, contém pelo menos 1 termo do vocabulário
2. **Pré-header** — 1 linha que complementa o subject (~80 char)
3. **Abertura** — reconhecer a dor principal em 2 linhas (não vender ainda)
4. **Corpo** — 3 parágrafos curtos:
   - Quem você é e por que tá falando disso
   - Uma das `duvidas_frequentes` respondida em 2-3 linhas (entrega de valor imediata)
   - O que vem na próxima semana de emails
5. **CTA suave** — não tem oferta de venda, só um próximo passo (responder, ler artigo, seguir IG)
6. **P.S.** — 1 frase memorável que reforça a promessa

**Regras:**
- Português BR coloquial, "você" não "tu"
- Parágrafos de 1-3 linhas (lê no celular)
- Zero jargão de marketing ("alavancar", "escalar", "transformar")
- Soar humano, não automático

**Formato de saída:**

```
## Subject recomendado
[subject]

## Pré-header
[preheader]

## Corpo do email
[email completo formatado]

## 3 Subjects alternativos pra A/B test
1. [alt 1]
2. [alt 2]
3. [alt 3]

## Notas estratégicas
[2-3 bullets explicando as escolhas: qual dor ativou, qual termo do vocabulário usou, por que esse CTA]
```
