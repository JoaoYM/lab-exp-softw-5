# Análise Estatística — GitHub REST (v3) vs GraphQL (v4)

**Data da execução:** 2026-07-03 18:44:13
**Arquivo de dados:** `resultados.csv`
**Nível de significância:** 0.05

## 1. Remoção de Outliers (Pareada)

| Indicador | Valor |
|---|---|
| Repositórios antes da limpeza | 29 |
| Repositórios removidos (outlier) | 8 (27.6%) |
| Repositórios mantidos | 21 |

> **Metodologia:** Para cada linguagem, calculou-se o IQR das 4 métricas (REST_tempo, GraphQL_tempo, REST_tamanho, GraphQL_tamanho). Se qualquer métrica de um repositório foi considerada outlier, o repositório inteiro (REST + GraphQL) foi descartado, garantindo pareamento 1:1.

## 2. Validação de Pareamento

| Linguagem | REST | GraphQL | Status |
|---|---|---|---|
| Go | 2 | 2 | ✅ OK |
| JavaScript | 3 | 3 | ✅ OK |
| Python | 10 | 10 | ✅ OK |
| TypeScript | 6 | 6 | ✅ OK |

**✅ Pareamento GLOBAL OK:** REST (21) == GraphQL (21)

## 3. RQ1 — Tempo de Resposta (ms)

| Linguagem | REST μ (ms) | GraphQL μ (ms) | Diferença (ms) | Diferença (%) | p-value | U | Signif. |
|---|---|---|---|---|---|---|---|
| Go | 78235.02 | 11436.46 | 66798.56 | 85.4% | 0.166667 | 0.0 | Não ❌ |
| JavaScript | 80987.29 | 12426.63 | 68560.66 | 84.7% | 0.050000 | 0.0 | Não ❌ |
| Python | 80100.59 | 12326.64 | 67773.95 | 84.6% | 0.000091 | 0.0 | Sim ✅ |
| TypeScript | 78848.13 | 11990.35 | 66857.78 | 84.8% | 0.001082 | 0.0 | Sim ✅ |

## 4. RQ2 — Tamanho do Payload (bytes)

| Linguagem | REST μ (bytes) | GraphQL μ (bytes) | Diferença (bytes) | Diferença (%) | p-value | U | Signif. |
|---|---|---|---|---|---|---|---|
| Go | 720323.00 | 58118.00 | 662205.00 | 91.9% | 0.666667 | 2.0 | Não ❌ |
| JavaScript | 251975.67 | 67872.33 | 184103.34 | 73.1% | 0.350000 | 3.0 | Não ❌ |
| Python | 327010.30 | 63117.70 | 263892.60 | 80.7% | 0.515075 | 50.0 | Não ❌ |
| TypeScript | 190081.17 | 60836.33 | 129244.84 | 68.0% | 0.531385 | 18.0 | Não ❌ |

## 5. Resumo Geral

| Indicador | Valor |
|---|---|
| Total de amostras | 42 |
| Amostras REST | 21 |
| Amostras GraphQL | 21 |
| Linguagens | 4 |
| Repositórios | 21 |

**RQ1 — Tempo:** 2/4 linguagens com diferença significativa.
**RQ2 — Tamanho:** 0/4 linguagens com diferença significativa.

## 6. Conclusão

- ⚠️ **RQ1:** GraphQL é mais rápido em 2/4 linguagens. Resultado misto.
- ❌ **RQ2:** Não há evidência significativa de que GraphQL tenha payload menor que REST.

---
*Relatório gerado automaticamente pelo script de análise estatística.*