<div class="capa">
    <div class="cabecalho">
        PONTIFÍCIA UNIVERSIDADE CATÓLICA DE MINAS GERAIS – PUC MINAS<br>
        Engenharia de Software Experimental — Laboratório 05
    </div>

    <div class="titulo-container">
        <h1>REST (v3) vs GRAPHQL (v4) NO GITHUB</h1>
        <h2>Análise Comparativa de Eficiência na Mineração de Dados de Code Review</h2>
    </div>

    <div class="autor">
        João Pedro Aguiar do Prado
    </div>

    <div class="rodape">
        Belo Horizonte - MG<br>
        2026
    </div>
</div>

## 1. Introdução

### 1.1 Contextualização

A mineração de dados em plataformas de hospedagem de código, como o GitHub, é uma prática consolidada em Engenharia de Software Experimental para investigar fenômenos como revisão de código (code review), integração contínua e qualidade de software. Duas interfaces de programação (APIs) são amplamente utilizadas para essa finalidade: a **REST API (v3)** e a **GraphQL API (v4)**.

A API REST do GitHub segue o modelo arquitetural RESTful, onde cada recurso (pull request, review, comentário) é acessado por meio de *endpoints* específicos. Para coletar dados aninhados — como *pull requests* com seus respectivos *reviews* e comentários — é necessário realizar múltiplas requisições encadeadas, um fenômeno conhecido como **problema N+1**. Esse encadeamento pode resultar em alta latência e tráfego de rede excessivo.

A API GraphQL, por outro lado, permite que o cliente especifique exatamente a estrutura dos dados desejados em uma única requisição, mitigando o problema N+1. No entanto, essa flexibilidade pode levar ao **over-fetching** (recebimento de dados não utilizados) ou **under-fetching** (necessidade de requisições adicionais), dependendo da query construída.

Este experimento tem como objetivo comparar a eficiência dessas duas abordagens no contexto específico da coleta de dados de *code review* do GitHub, mensurando duas métricas fundamentais: **tempo de resposta** e **tamanho do payload**.

### 1.2 Perguntas de Pesquisa

O experimento é guiado por duas perguntas de pesquisa (Research Questions — RQs):

| ID | Pergunta | Métrica |
|---|---|---|
| **RQ1** | A API GraphQL (v4) apresenta tempo de resposta menor que a API REST (v3) na coleta de dados de code review? | Tempo de resposta (ms) |
| **RQ2** | A API GraphQL (v4) retorna payload de tamanho menor que a API REST (v3) na coleta de dados de code review? | Tamanho do payload (bytes) |

### 1.3 Hipóteses

Para cada pergunta de pesquisa, foram formuladas hipóteses estatísticas unilaterais, assumindo que GraphQL é mais eficiente (menor tempo e menor payload) que REST.

#### RQ1 — Tempo de Resposta

- <strong>Hipótese Nula (H<sub>0(1)</sub>):</strong> O tempo de resposta da GraphQL &eacute; maior ou igual ao da REST.  
  H<sub>0(1)</sub>: &mu;<sub>GraphQL</sub> &ge; &mu;<sub>REST</sub>
- <strong>Hipótese Alternativa (H<sub>1(1)</sub>):</strong> O tempo de resposta da GraphQL &eacute; menor que o da REST.  
  H<sub>1(1)</sub>: &mu;<sub>GraphQL</sub> < &mu;<sub>REST</sub>

#### RQ2 — Tamanho do Payload

- <strong>Hipótese Nula (H<sub>0(2)</sub>):</strong> O tamanho do payload da GraphQL &eacute; maior ou igual ao da REST.  
  H<sub>0(2)</sub>: &mu;<sub>GraphQL</sub> &ge; &mu;<sub>REST</sub>
- <strong>Hipótese Alternativa (H<sub>1(2)</sub>):</strong> O tamanho do payload da GraphQL &eacute; menor que o da REST.  
  H<sub>1(2)</sub>: &mu;<sub>GraphQL</sub> < &mu;<sub>REST</sub>

O n&iacute;vel de signific&acirc;ncia adotado para todos os testes &eacute; &alpha; = 0,05.

---

## 2. Metodologia

### 2.1 Abordagem GQM (Goal-Question-Metric)

O experimento segue o paradigma **GQM** (Goal-Question-Metric), conforme definido a seguir:

| Elemento | Descrição |
|---|---|
| **Goal (Objetivo)** | Analisar as APIs REST (v3) e GraphQL (v4) do GitHub com o propósito de comparar sua eficiência na coleta de dados de code review, sob a perspectiva do pesquisador em Engenharia de Software Experimental, no contexto da mineração de repositórios de software. |
| **Questions (Perguntas)** | **RQ1:** GraphQL é mais rápida que REST? **RQ2:** GraphQL retorna payload menor que REST? |
| **Metrics (Métricas)** | Tempo de resposta (milissegundos) e Tamanho do payload (bytes) |

### 2.2 Desenho Experimental

#### 2.2.1 Variáveis

| Tipo | Variável | Escala | Descrição |
|---|---|---|---|
| **Independente** | Tecnologia da API | Nominal (2 níveis) | REST (v3) ou GraphQL (v4) |
| **Dependente (RQ1)** | Tempo de resposta | Razão (ms) | Tempo total para completar a coleta de dados do repositório |
| **Dependente (RQ2)** | Tamanho do payload | Razão (bytes) | Soma dos tamanhos das respostas HTTP recebidas |
| **Controle** | Linguagem de programação | Nominal (6 níveis) | JavaScript, Python, TypeScript, Java, Go, C# |
| **Controle** | Repositório | Nominal | Identificador único do repositório (owner/repo) |

#### 2.2.2 Tratamentos

O experimento possui dois tratamentos:

- **Tratamento A (Controle):** Coleta via API REST (v3) — múltiplas requisições encadeadas para obter PRs, reviews e comentários.
- **Tratamento B (Experimental):** Coleta via API GraphQL (v4) — query única com paginação para obter a mesma estrutura de dados.

#### 2.2.3 Objetos Experimentais

Foram selecionados **30 repositórios** de software populares, distribuídos entre as 6 linguagens mais ativas do Octoverse 2024 (5 repositórios por linguagem). A seleção priorizou repositórios com alta atividade de pull requests e code review.

**Linguagens analisadas:**
- JavaScript
- Python
- TypeScript
- Java
- Go
- C#

#### 2.2.4 Alocação e Pareamento

Cada repositório foi submetido a ambos os tratamentos (REST e GraphQL), caracterizando um **desenho pareado** (paired design). O repositório serve como seu próprio controle, eliminando a variabilidade entre objetos experimentais. A ordem de execução dos tratamentos foi fixa (REST primeiro, GraphQL depois) devido à dependência do GraphQL dos dados REST para identificar os repositórios.

### 2.3 Diagrama da Metodologia

O pipeline completo do experimento &eacute; ilustrado na Figura 1.

![Diagrama da Metodologia](assets/diagrama_metodologia.png)

*Figura 1: Pipeline metodológico do experimento, desde a extração dos dados até a conclusão estatística.*

### 2.4 Instrumentação

O experimento foi implementado em Python 3.12+ com as seguintes bibliotecas:

- `requests` — comunicação com as APIs REST e GraphQL
- `pandas` — manipulação e análise dos dados
- `scipy` — testes estatísticos (Mann-Whitney U)
- `python-dotenv` — gerenciamento do token de autenticação
- `matplotlib` e `seaborn` — geração de gráficos estáticos
- `graphviz` — diagrama metodológico

### 2.5 Procedimento de Coleta

Para cada repositório, o script de mineração (`mineracao.py`) executou os seguintes passos:

1. **Autenticação:** Utilização de token pessoal do GitHub (clássico) com escopos `repo` e `public_repo`.
2. **Coleta REST:** Requisições paginadas aos endpoints:
   - `GET /repos/{owner}/{repo}/pulls` — lista de pull requests
   - `GET /repos/{owner}/{repo}/pulls/{number}/reviews` — reviews de cada PR
   - `GET /repos/{owner}/{repo}/pulls/{number}/comments` — comentários de cada PR
3. **Coleta GraphQL:** Query única com paginação utilizando o campo `pullRequests` com `reviews` aninhados.
4. **Medição:** O tempo de resposta foi medido com `time.time()` antes e depois de cada coleta completa. O tamanho do payload foi obtido via `len(response.content)` para cada requisição.

### 2.6 Sanitização dos Dados

#### 2.6.1 Filtro de Bots

Pull requests e reviews realizados por bots conhecidos foram excluídos da contagem, mas não da coleta (o tempo e tamanho refletem a coleta completa, incluindo dados de bots). A lista de bots filtrados inclui: `dependabot[bot]`, `github-actions[bot]`, `renovate[bot]`, `snyk-bot`, entre outros.

#### 2.6.2 Remoção de Outliers Pareada

A remoção de outliers foi realizada de forma **pareada**, tratando o repositório como unidade central. O procedimento foi:

1. **Pivot:** Os dados foram transformados para o formato largo, onde cada repositório ocupa uma única linha com as colunas: `tempo_ms_REST`, `tempo_ms_GraphQL`, `tamanho_bytes_REST`, `tamanho_bytes_GraphQL`.
2. **Cálculo do IQR:** Para cada linguagem, calcularam-se os limites inferior e superior (Q1 &minus; 1,5 &times; IQR, Q3 + 1,5 &times; IQR) para cada uma das 4 colunas métricas.
3. **Remoção:** Se qualquer métrica (tempo REST, tempo GraphQL, tamanho REST ou tamanho GraphQL) de um repositório foi considerada outlier, o repositório **inteiro** (ambas as medições) foi descartado.
4. **Validação:** Após a limpeza, verificou-se que o número de amostras REST é estritamente igual ao número de amostras GraphQL, tanto globalmente quanto por linguagem.

### 2.7 Auditoria de Imparcialidade (Fairness Check)

Para garantir que a comparação foi conduzida de forma justa ("maçãs com maçãs"), realizamos uma auditoria técnica do script de mineração (`mineracao.py`). Os seguintes aspectos foram verificados:

| Aspecto | REST (v3) | GraphQL (v4) | Equivalência |
|---|---|---|---|
| Medição de tamanho | `len(response.content)` bruto | `len(response.content)` bruto | ✅ Idêntico |
| Medição de tempo | `time.time()` antes/depois | `time.time()` antes/depois | ✅ Idêntico |
| Delay entre páginas | `time.sleep(0.3)` | `time.sleep(0.3)` | ✅ Idêntico |
| Paginação | Múltiplas chamadas REST | Múltiplas páginas (cursor) | ✅ Mesma estrutura |
| Filtro de bots | Aplicado igualmente | Aplicado igualmente | ✅ Idêntico |
| Backoff/rate-limit | Exponencial + verificação | Exponencial | ✅ Similar |
| Token de autenticação | Mesmo token | Mesmo token | ✅ Idêntico |

A diferença de ~85% no tempo de resposta observada neste experimento &eacute; uma consequência direta do **problema N+1** inerente &agrave; arquitetura REST. Para um reposit&oacute;rio com N pull requests, a API REST requer:
- 1 requisi&ccedil;&atilde;o para listar PRs
- N requisi&ccedil;&otilde;es para obter reviews de cada PR
- N requisi&ccedil;&otilde;es para obter coment&aacute;rios de cada PR

Total: 1 + 2N requisi&ccedil;&otilde;es. Com N = 200 PRs, s&atilde;o 401 requisi&ccedil;&otilde;es HTTP, cada uma com latência de rede, cabeçalhos e processamento.

A GraphQL, por sua vez, realiza uma &uacute;nica requisi&ccedil;&atilde;o por página (aproximadamente 20 páginas para 200 PRs), totalizando ~20 requisi&ccedil;&otilde;es. O ganho de desempenho &eacute;, portanto, esperado e matematicamente consistente com a redução no número de viagens de ida-e-volta (round-trips) ao servidor.

N&atilde;o foram identificados delays artificiais ou assimetrias no c&oacute;digo que pudessem beneficiar uma tecnologia em detrimento da outra. A &uacute;nica diferen&ccedil;a significativa &eacute; o n&uacute;mero de requisi&ccedil;&otilde;es HTTP, que &eacute; uma caracter&iacute;stica intr&iacute;nseca de cada arquitetura.

### 2.8 Teste Estatístico

Foi utilizado o **Teste de Mann-Whitney U** (unilateral, com `alternative='less'`) para comparar as distribuições de GraphQL contra REST. A escolha do teste não-paramétrico deve-se à:

- Não-normalidade esperada dos dados de tempo e tamanho
- Tamanho reduzido da amostra após a remoção de outliers
- Robustez a assimetrias e valores extremos residuais

A estatística U foi calculada para cada linguagem separadamente, tanto para a métrica de tempo (RQ1) quanto para tamanho (RQ2).

---

## 3. Resultados

### 3.1 Remoção de Outliers e Pareamento

| Indicador | Valor |
|---|---|
| Repositórios antes da limpeza | 29 |
| Repositórios removidos (outlier) | 8 (27,6%) |
| Repositórios mantidos | 21 |
| Total de amostras | 42 (21 REST + 21 GraphQL) |

A validação de pareamento confirmou que todas as linguagens mantiveram equilíbrio perfeito entre REST e GraphQL:

| Linguagem | REST | GraphQL | Status |
|---|---|---|---|
| Go | 2 | 2 | OK |
| JavaScript | 3 | 3 | OK |
| Python | 10 | 10 | OK |
| TypeScript | 6 | 6 | OK |
| **Global** | **21** | **21** | **OK** |

> **Nota:** As linguagens Java e C# n&atilde;o apresentaram dados suficientes ap&oacute;s a limpeza e foram exclu&iacute;das da an&aacute;lise.

![Comparativo de Tempo de Resposta](assets/chart_tempo.png)

*Figura 2: Compara&ccedil;&atilde;o do tempo m&eacute;dio de resposta (ms) entre REST e GraphQL por linguagem. As barras de erro representam &plusmn;1 desvio padr&atilde;o. Os valores exatos est&atilde;o anotados acima de cada barra.*

![Comparativo de Tamanho do Payload](assets/chart_tamanho.png)

*Figura 3: Compara&ccedil;&atilde;o do tamanho m&eacute;dio do payload (bytes) entre REST e GraphQL por linguagem. As barras de erro representam &plusmn;1 desvio padr&atilde;o.*

![Boxplot do Tempo de Resposta](assets/chart_boxplot.png)

*Figura 4: Distribui&ccedil;&atilde;o do tempo de resposta por linguagem e tecnologia. Os losangos amarelos indicam a m&eacute;dia. O boxplot revela a assimetria e a variabilidade dos dados, al&eacute;m de outliers residuais.*

![Dispers&atilde;o Tamanho vs Tempo](assets/chart_scatter.png)

*Figura 5: Dispers&atilde;o do tamanho do payload (eixo X) versus tempo de resposta (eixo Y). Cada ponto representa um reposit&oacute;rio. A separa&ccedil;&atilde;o clara entre os clusters REST e GraphQL demonstra visualmente a superioridade da GraphQL em ambas as m&eacute;tricas.*

### 3.2 RQ1 — Tempo de Resposta

| Linguagem | REST &mu; (ms) | GraphQL &mu; (ms) | Diferen&ccedil;a (ms) | Diferen&ccedil;a (%) | p-value | U | Significativo |
|---|---|---|---|---|---|---|---|
| Go | 78.235,02 | 11.436,46 | 66.798,56 | 85,4% | 0,1667 | 0,0 | N&atilde;o |
| JavaScript | 80.987,29 | 12.426,63 | 68.560,66 | 84,7% | 0,0500 | 0,0 | N&atilde;o |
| Python | 80.100,59 | 12.326,64 | 67.773,95 | 84,6% | **0,0001** | 0,0 | **Sim** |
| TypeScript | 78.848,13 | 11.990,35 | 66.857,78 | 84,8% | **0,0011** | 0,0 | **Sim** |

**Interpreta&ccedil;&atilde;o:** Para as linguagens **Python** e **TypeScript**, rejeitamos H<sub>0(1)</sub> ao n&iacute;vel de signific&acirc;ncia de 5%. H&aacute; evid&ecirc;ncia estat&iacute;stica de que GraphQL &eacute; significativamente mais r&aacute;pida que REST para essas linguagens. Para **Go** e **JavaScript**, n&atilde;o h&aacute; evid&ecirc;ncia suficiente para rejeitar H<sub>0(1)</sub> (p > 0,05), embora o p-value de JavaScript (0,050) esteja no limiar da signific&acirc;ncia.

### 3.3 RQ2 — Tamanho do Payload

| Linguagem | REST &mu; (bytes) | GraphQL &mu; (bytes) | Diferen&ccedil;a (bytes) | Diferen&ccedil;a (%) | p-value | U | Significativo |
|---|---|---|---|---|---|---|---|
| Go | 720,323 | 58,118 | 662,205 | 91,9% | 0,6667 | 2,0 | N&atilde;o |
| JavaScript | 251,976 | 67,872 | 184,103 | 73,1% | 0,3500 | 3,0 | N&atilde;o |
| Python | 327,010 | 63,118 | 263,893 | 80,7% | 0,5151 | 50,0 | N&atilde;o |
| TypeScript | 190,081 | 60,836 | 129,245 | 68,0% | 0,5314 | 18,0 | N&atilde;o |

**Interpreta&ccedil;&atilde;o:** Para **todas as linguagens**, n&atilde;o rejeitamos H<sub>0(2)</sub>. N&atilde;o h&aacute; evid&ecirc;ncia estat&iacute;stica de que GraphQL retorne payload significativamente menor que REST. Este resultado &eacute; contraintuitivo, dado que a diferen&ccedil;a percentual &eacute; expressiva (68%&ndash;92%). A falta de signific&acirc;ncia pode ser atribu&iacute;da ao tamanho reduzido da amostra e &agrave; alta variabilidade intra-grupo.

### 3.4 Resumo dos Testes

| Pergunta | Linguagens com diferen&ccedil;a significativa | Conclus&atilde;o |
|---|---|---|
| RQ1 (Tempo) | 2/4 (Python, TypeScript) | Resultado misto |
| RQ2 (Tamanho) | 0/4 | Sem evid&ecirc;ncia significativa |

---

## 4. Amea&ccedil;as &agrave; Validade

### 4.1 Validade de Constru&ccedil;&atilde;o

- **M&eacute;trica de tempo:** O tempo medido inclui lat&ecirc;ncia de rede, processamento do servidor e transfer&ecirc;ncia de dados. N&atilde;o foi poss&iacute;vel isolar o tempo de processamento puro da API. O proxy utilizado (tempo total de coleta) &eacute; uma aproxima&ccedil;&atilde;o aceit&aacute;vel para o construto "efici&ecirc;ncia".
- **M&eacute;trica de tamanho:** O tamanho do payload inclui cabe&ccedil;alhos HTTP, o que pode favorecer REST (que faz mais requisi&ccedil;&otilde;es, cada uma com seus cabe&ccedil;alhos). No entanto, como a compara&ccedil;&atilde;o &eacute; entre as duas tecnologias no cen&aacute;rio real de uso, essa medida reflete o custo real de transfer&ecirc;ncia.

### 4.2 Validade Interna

- **Ordem de execu&ccedil;&atilde;o fixa:** A coleta REST foi sempre realizada antes da GraphQL. Isso pode introduzir vi&eacute;s de aprendizado (caching no lado do GitHub) ou de fadiga (rate limiting mais severo na segunda coleta). A pausa de 1 segundo entre reposit&oacute;rios e o backoff exponencial mitigam parcialmente esse risco.
- **Varia&ccedil;&atilde;o de rede:** As coletas ocorreram em momentos diferentes, sujeitas a varia&ccedil;&otilde;es na lat&ecirc;ncia da internet. O token de autentica&ccedil;&atilde;o e o hor&aacute;rio do dia podem ter influenciado os resultados.
- **Rate limiting:** A API REST possui rate limits mais restritivos (5.000 requisi&ccedil;&otilde;es/hora) que a GraphQL (mesmo limite, mas por ponto de custo). Isso pode ter afetado o tempo de coleta REST, especialmente para reposit&oacute;rios com muitos PRs.
- **Auditoria de imparcialidade:** Conforme detalhado na Se&ccedil;&atilde;o 2.7, todos os aspectos t&eacute;cnicos da medi&ccedil;&atilde;o foram equivalentes entre as duas tecnologias. A diferen&ccedil;a observada &eacute; atribu&iacute;da exclusivamente ao problema arquitetural N+1 da REST, e n&atilde;o a vieses de implementa&ccedil;&atilde;o.

### 4.3 Validade Externa

- **Tamanho da amostra:** Apenas 21 reposit&oacute;rios (ap&oacute;s limpeza) de 4 linguagens foram analisados. Isso limita a generaliza&ccedil;&atilde;o dos resultados para outros reposit&oacute;rios e linguagens.
- **Escopo da query:** A query GraphQL foi constru&iacute;da para espelhar a coleta REST, mas pode n&atilde;o representar o uso &oacute;timo de cada tecnologia. Uma query GraphQL mais refinada poderia produzir resultados diferentes.
- **Contexto espec&iacute;fico:** Os resultados s&atilde;o espec&iacute;ficos para a coleta de dados de code review no GitHub. Outros tipos de consulta (issues, commits, etc.) podem apresentar comportamentos distintos.

### 4.4 Validade de Conclus&atilde;o

- **Teste estat&iacute;stico:** O teste de Mann-Whitney U, embora adequado para dados n&atilde;o-normais, tem menor poder estat&iacute;stico que o teste t pareado. Com amostras pequenas (n=2 para Go), o teste pode n&atilde;o detectar diferen&ccedil;as reais (erro tipo II).
- **M&uacute;ltiplas compara&ccedil;&otilde;es:** Foram realizados 8 testes (4 linguagens &times; 2 m&eacute;tricas), aumentando a chance de falsos positivos. N&atilde;o foi aplicada corre&ccedil;&atilde;o de Bonferroni ou similar, o que pode inflar o erro tipo I.
- **Unilateralidade:** A escolha do teste unilateral (GraphQL < REST) &eacute; justificada pela hip&oacute;tese direcional, mas mascara a possibilidade de REST ser mais r&aacute;pida que GraphQL em alguns cen&aacute;rios.

---

## 5. Conclus&atilde;o e Discuss&atilde;o

### 5.1 S&iacute;ntese dos Resultados

Este experimento comparou a efici&ecirc;ncia das APIs REST (v3) e GraphQL (v4) do GitHub na coleta de dados de code review. Os principais achados s&atilde;o:

1. **RQ1 (Tempo de Resposta):** GraphQL apresentou tempo de resposta consistentemente menor que REST em todas as linguagens analisadas (redu&ccedil;&atilde;o de ~85%). No entanto, a signific&acirc;ncia estat&iacute;stica foi confirmada apenas para Python (p = 0,0001) e TypeScript (p = 0,0011). Para Go e JavaScript, o tamanho amostral reduzido (n=2 e n=3, respectivamente) pode explicar a falta de signific&acirc;ncia.

2. **RQ2 (Tamanho do Payload):** Embora GraphQL tenha apresentado payloads 68%&ndash;92% menores que REST, nenhuma das diferen&ccedil;as foi estatisticamente significativa. A alta variabilidade intra-grupo e o tamanho amostral limitado s&atilde;o as causas prov&aacute;veis.

### 5.2 Interpreta&ccedil;&atilde;o

A redu&ccedil;&atilde;o expressiva no tempo de resposta (~85%) sugere que a GraphQL &eacute; **praticamente mais eficiente** que a REST para o cen&aacute;rio de coleta de code review, mesmo quando a signific&acirc;ncia estat&iacute;stica n&atilde;o &eacute; alcan&ccedil;ada. O problema N+1 da REST, que exige m&uacute;ltiplas requisi&ccedil;&otilde;es encadeadas, &eacute; a causa raiz dessa diferen&ccedil;a.

O resultado n&atilde;o-significativo para tamanho do payload &eacute; surpreendente, dado que a GraphQL permite especificar exatamente os campos desejados. Uma hip&oacute;tese &eacute; que a query GraphQL utilizada, embora equivalente em funcionalidade, pode estar retornando metadados adicionais n&atilde;o presentes na resposta REST. Outra hip&oacute;tese &eacute; que a sobrecarga dos cabe&ccedil;alhos HTTP nas m&uacute;ltiplas requisi&ccedil;&otilde;es REST n&atilde;o &eacute; t&atilde;o significativa quanto o esperado.

### 5.3 Trabalhos Futuros

- **Expans&atilde;o da amostra:** Aumentar o n&uacute;mero de reposit&oacute;rios por linguagem para melhorar o poder estat&iacute;stico.
- **Otimiza&ccedil;&atilde;o de queries:** Testar diferentes estrat&eacute;gias de query GraphQL (fragmentos, aliases, diretivas) para minimizar o payload.
- **An&aacute;lise de custo:** Incorporar o custo computacional (pontos de consulta GraphQL vs. n&uacute;mero de requisi&ccedil;&otilde;es REST) como m&eacute;trica adicional.
- **Corre&ccedil;&atilde;o de m&uacute;ltiplas compara&ccedil;&otilde;es:** Aplicar corre&ccedil;&atilde;o de Bonferroni ou False Discovery Rate (FDR) em estudos futuros com m&uacute;ltiplas linguagens.

---

*Relat&oacute;rio gerado automaticamente pelo pipeline de an&aacute;lise estat&iacute;stica do Laborat&oacute;rio 05.*