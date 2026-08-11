---
name: cookia-copy
description: Gera copy de conversão (headlines, emails, VSL, landing, bullets, CTA, FAQ, garantia, objeções) consumindo um dossiê do Cookia. Cada output usa o vocabulário real, dor principal e objeções extraídas do público-alvo brasileiro. Use quando o usuário pedir copy de funil orgânico/owned, sequência de email, página de vendas, ou qualquer peça de conversão derivada de um dossiê Cookia já gerado.
---

# /cookia-copy — Copy de Conversão Dossiê-Driven

## Pré-requisito

Existir um dossiê em `data/dossies/<nicho>_<data>.md` (gerado pela skill `cookia`). Se não existir, perguntar o nicho e rodar `cookia` antes.

## Quando invocar

- "Escreve a headline da minha landing"
- "Quero email de boas-vindas pra esse nicho"
- "Gera bullets de oferta usando o dossiê de [nicho]"
- "Roteiro de VSL 90s"
- "Quebra de objeção pra essa lista"

## Catálogo de prompts (30 peças, 4 estágios de funil)

### Topo — captação (6)
1. `headline-landing` — Headline principal (5 variações + recomendada)
2. `sub-headline` — Sub-headline complementar
3. `lead-magnet-title` — Título de isca digital
4. `hook-organico` — Hook IG/LinkedIn (estágio unaware)
5. `bio-perfil` — Bio/headline de perfil social
6. `open-loop` — Hook 3s pra Reels/Shorts

### Meio — nutrição (8)
7. `email-boas-vindas` — Email D+0
8. `sequencia-nutricao-5` — 5 emails de nutrição
9. `subject-ab` — 10 subject lines A/B
10. `story-venda` — Roteiro de story IG
11. `carrossel-erros` — Carrossel "5 erros que…"
12. `post-prova-social` — Post de case
13. `vsl-hook-15s` — Hook de VSL
14. `roteiro-webinar` — Estrutura de webinar

### Fundo — conversão (10)
15. `pagina-oferta` — Página completa
16. `bullets-beneficio` — 10 bullets
17. `quebra-objecao` — 1 contra-argumento por objeção
18. `garantia` — Texto de garantia
19. `urgencia-etica` — Urgência sem mentir
20. `faq-vendas` — FAQ da página
21. `cta-botao` — 10 variações de CTA
22. `ps-email` — P.S. de email final
23. `bump-checkout` — Texto de bump
24. `pagina-obrigado` — TYP + upsell

### Retenção (6)
25. `carrinho-abandonado` — Email de recuperação
26. `reativacao-30d` — Sequência de reativação
27. `nps-contextual` — Pesquisa NPS
28. `pedido-depoimento` — Pedido de review
29. `wa-pos-compra` — Mensagem WhatsApp
30. `onboarding-3emails` — Onboarding em 3 emails

## Como usar

```
/cookia-copy <id-do-prompt> [caminho-do-dossiê]
```

Exemplos:
- `/cookia-copy headline-landing` → usa o dossiê mais recente automaticamente
- `/cookia-copy email-boas-vindas data/dossies/advocacia_2026-05-15.md`
- `/cookia-copy sequencia-nutricao-5 advocacia` → busca dossiê do nicho

## Output padrão

Toda peça vem com:
1. **3-10 variações** do output pedido
2. **1 recomendada** com justificativa
3. **Campos do dossiê consumidos** (transparência)
4. **Estágio de consciência** alvo (Schwartz)

## Anti-patterns

- Não usar promessa numérica inventada ("aumente 300%") — Cookia usa linguagem de processo
- Não copiar vocabulário só por copiar — sempre cruzar com tom da marca
- Não pular o dossiê — copy genérica sem `vocabulario_real` perde 70% da força
