---
name: radar-expand
description: Expande o dossiê do Radar de Demanda gerando MAIS ofertas, variações, exploração de dores específicas, mudança de ticket ou formato — SEM rodar o pipeline completo (não raspa de novo, custo ~R$3-5 por chamada vs R$20 do dossiê inteiro). Use quando o usuário quer mais opções, ver variações da oferta X, atacar uma dor que não foi explorada, baixar/subir ticket ou trocar formato.
---

# /radar-expand — Brainstorm infinito sobre dossiê existente

## Pré-requisito

Ter rodado `python scripts/radar_run.py "<nicho>"` antes (precisa do JSON salvo em `data/dossies/`).

## 5 comandos disponíveis

### 1. Gerar 5 ofertas novas com ângulos diferentes
```
python scripts/radar_expand.py mais-ofertas
```
**Custo:** ~R$5
**Output:** 5 ofertas explorando ângulos não usados antes + dores secundárias + formatos diferentes.

### 2. Gerar 3 variações de uma oferta específica
```
python scripts/radar_expand.py variar 1
```
(troca o `1` pelo ID da oferta que quer variar)

**Custo:** ~R$3
**Output:** 3 variações mantendo dor + público, mudando ângulo/formato/ticket.

### 3. Explorar uma dor que não foi atacada
```
python scripts/radar_expand.py explorar-dor 4
```
(troca o `4` pelo rank da dor que quer explorar — Bleeding Neck que ficou de fora)

**Custo:** ~R$4
**Output:** 3 ofertas focadas naquela dor (entrada + core + premium).

### 4. Mudar ticket das ofertas
```
python scripts/radar_expand.py reprice "R$197"
```

**Custo:** ~R$3
**Output:** 5 ofertas calibradas pro novo ticket (formato/entrega/profundidade ajustados).

### 5. Mudar formato das ofertas
```
python scripts/radar_expand.py formato "mentoria"
```
(ex: `mentoria`, `comunidade`, `template`, `checklist`, `ebook`, `consultoria`)

**Custo:** ~R$3
**Output:** 5 ofertas no formato escolhido.

## Output

Cada comando gera um arquivo JSON novo em `data/dossies/<nicho>_<ts>_<tipo>_<hora>.json`.
O dossiê original NÃO é sobrescrito.

## Custo total quando usado muito

| Cenário | Chamadas | Custo total |
|---|---|---|
| 1 dossiê completo | 1 run | ~R$20 |
| Dossiê + 3 expansões | 1 run + 3 expand | ~R$30 |
| Dossiê + 10 expansões (uso pesado) | 1 run + 10 expand | ~R$55 |

**É MUITO mais barato explorar variações que rodar dossiê novo.**

## Anti-patterns

- ❌ Rodar `radar_run` várias vezes pra ter mais ofertas — use `expand` (15x mais barato)
- ❌ Expandir dossiê velho (>30 dias) sem rodar novo primeiro — sinais defasaram
- ❌ Pedir formato sem fit com nicho (ex: "comunidade" pra produto físico)
