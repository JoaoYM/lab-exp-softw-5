#!/usr/bin/env python3
"""
Script de Análise Estatística — GitHub REST (v3) vs GraphQL (v4)
=================================================================
Laboratório 05 — Comparação de eficiência entre APIs do GitHub.

Este script:
1. Lê o arquivo resultados.csv gerado pelo mineracao.py
2. Remove outliers de forma PAREADA (repositório como unidade):
   - Pivota os dados para que cada repositório tenha REST e GraphQL na mesma linha
   - Aplica IQR por linguagem em TODAS as 4 colunas (REST_tempo, GraphQL_tempo,
     REST_tamanho, GraphQL_tamanho)
   - Se QUALQUER métrica do repositório for outlier → repositório inteiro é descartado
   - Retorna ao formato longo para o restante da análise
3. Valida o pareamento (REST == GraphQL) globalmente e por linguagem
4. Executa o Teste de Mann-Whitney para validar significância estatística
5. Exibe médias por linguagem e p-values para RQ1 e RQ2

Uso:
    python analise.py

Requer:
    - pandas, scipy
    - Arquivo resultados.csv (gerado pelo mineracao.py)
"""

import sys
import logging
from pathlib import Path

import pandas as pd
from scipy.stats import mannwhitneyu

# ──────────────────────────────────────────────────────────────────────
# Configuração de Logging
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Constantes (caminhos relativos à nova estrutura)
# ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_CSV = str(BASE_DIR / "data" / "resultados.csv")
ARQUIVO_MD = str(BASE_DIR / "docs" / "resultados_analise.md")
NIVEL_SIGNIFICANCIA = 0.05


# ──────────────────────────────────────────────────────────────────────
# Funções de Análise
# ──────────────────────────────────────────────────────────────────────

def carregar_dados(caminho: str) -> pd.DataFrame:
    """
    Carrega o arquivo CSV de resultados.
    Retorna um DataFrame pandas.
    """
    if not Path(caminho).exists():
        logger.error(f"Arquivo {caminho} não encontrado. Execute mineracao.py primeiro.")
        sys.exit(1)

    df = pd.read_csv(caminho)
    logger.info(f"Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
    logger.info(f"Colunas: {list(df.columns)}")
    logger.info(f"Tecnologias: {df['tecnologia'].unique()}")
    logger.info(f"Linguagens: {df['linguagem'].unique()}")
    return df


def remover_outliers_pareado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove outliers de forma PAREADA, tratando o repositório como unidade
    central da análise.

    METODOLOGIA:
    ────────────
    1. Pivot: transforma os dados do formato longo para o formato largo,
       onde cada repositório ocupa uma única linha com colunas:
         - tempo_ms_REST, tempo_ms_GraphQL
         - tamanho_bytes_REST, tamanho_bytes_GraphQL

    2. Para cada linguagem, calcula os limites IQR (Q1 - 1.5*IQR, Q3 + 1.5*IQR)
       para cada uma das 4 colunas métricas.

    3. Se a medição de REST OU GraphQL (seja tempo ou tamanho) de um
       determinado repositório for considerada outlier, o repositório
       INTEIRO (ambas as medições) é descartado.

    4. Retorna ao formato longo (melt) para manter compatibilidade com
       o restante do pipeline (cálculo de médias, Mann-Whitney, etc.).

    Args:
        df: DataFrame no formato longo com colunas:
            repositorio, linguagem, tecnologia, tempo_ms, tamanho_bytes

    Returns:
        DataFrame limpo, ainda no formato longo, mas com pareamento
        garantido (REST == GraphQL).
    """
    logger.info("=" * 60)
    logger.info("ETAPA: Remoção de Outliers Pareada (IQR)")
    logger.info("=" * 60)

    # ── 1. Pivot: cada repositório vira uma linha única ──────────────
    # Antes do pivot, verificamos se há duplicatas (ex: mesmo repositório
    # aparecendo mais de uma vez para a mesma tecnologia). Se houver,
    # tiramos a média como medida de agregação segura.
    df_pivot = df.pivot_table(
        index=['repositorio', 'linguagem'],
        columns='tecnologia',
        values=['tempo_ms', 'tamanho_bytes'],
        aggfunc='mean'  # Seguro: se houver duplicatas, média é usada
    )

    # Achata o MultiIndex das colunas: ('tempo_ms', 'REST') → 'tempo_ms_REST'
    df_pivot.columns = [f'{metrica}_{tec}' for metrica, tec in df_pivot.columns]
    df_pivot = df_pivot.reset_index()

    n_repos_antes = len(df_pivot)
    logger.info(f"Repositórios antes da limpeza: {n_repos_antes}")

    # ── 2. Aplica IQR por linguagem em todas as 4 colunas métricas ──
    colunas_metricas = [
        'tempo_ms_REST',
        'tempo_ms_GraphQL',
        'tamanho_bytes_REST',
        'tamanho_bytes_GraphQL',
    ]

    # Flag booleana: True se o repositório for outlier em QUALQUER métrica
    df_pivot['is_outlier'] = False

    for linguagem in sorted(df_pivot['linguagem'].unique()):
        mask_ling = df_pivot['linguagem'] == linguagem
        grupo = df_pivot.loc[mask_ling]

        for col in colunas_metricas:
            Q1 = grupo[col].quantile(0.25)
            Q3 = grupo[col].quantile(0.75)
            IQR = Q3 - Q1

            limite_inferior = Q1 - 1.5 * IQR
            limite_superior = Q3 + 1.5 * IQR

            # Identifica quais repositórios são outlier nesta coluna
            eh_outlier = (grupo[col] < limite_inferior) | (grupo[col] > limite_superior)
            repos_outlier = grupo.loc[eh_outlier, 'repositorio'].tolist()

            if repos_outlier:
                logger.debug(
                    f"  [{linguagem}] {col}: {len(repos_outlier)} repositório(s) "
                    f"outlier → {repos_outlier}"
                )
                # Marca o repositório inteiro para remoção
                df_pivot.loc[df_pivot['repositorio'].isin(repos_outlier), 'is_outlier'] = True

    # ── 3. Remove repositórios marcados como outlier ─────────────────
    df_pivot_limpo = df_pivot[~df_pivot['is_outlier']].copy()
    n_repos_removidos = n_repos_antes - len(df_pivot_limpo)

    logger.info(
        f"Repositórios removidos (outlier em qualquer métrica): "
        f"{n_repos_removidos} ({n_repos_removidos / n_repos_antes * 100:.1f}%)"
    )
    logger.info(
        f"Repositórios mantidos: {len(df_pivot_limpo)} "
        f"(cada um com 1 linha REST + 1 linha GraphQL)"
    )

    # Drop da coluna auxiliar
    df_pivot_limpo.drop(columns=['is_outlier'], inplace=True)

    # ── 4. Retorna ao formato longo (melt) ───────────────────────────
    # Derrete as 4 colunas métricas em duas colunas: 'variavel' e 'valor'
    df_long = df_pivot_limpo.melt(
        id_vars=['repositorio', 'linguagem'],
        value_vars=colunas_metricas,
        var_name='variavel',
        value_name='valor',
    )

    # Extrai 'tecnologia' e 'metrica' do nome composto da variável
    # Ex: 'tempo_ms_REST' → metrica='tempo_ms', tecnologia='REST'
    df_long['tecnologia'] = df_long['variavel'].apply(lambda x: x.split('_')[-1])
    # Remove o sufixo da tecnologia para obter o nome da métrica
    # Ex: 'tempo_ms_REST' → remove '_REST' → 'tempo_ms'
    df_long['metrica'] = df_long.apply(
        lambda row: row['variavel'].replace(f"_{row['tecnologia']}", ''),
        axis=1
    )

    # Separa as linhas de tempo e tamanho em DataFrames distintos
    df_tempo = (
        df_long[df_long['metrica'] == 'tempo_ms']
        .rename(columns={'valor': 'tempo_ms'})
        .drop(columns=['variavel', 'metrica'])
    )

    df_tamanho = (
        df_long[df_long['metrica'] == 'tamanho_bytes']
        .rename(columns={'valor': 'tamanho_bytes'})
        .drop(columns=['variavel', 'metrica'])
    )

    # Faz merge para recompor o formato longo original
    # (cada linha = 1 repositório + 1 tecnologia + tempo + tamanho)
    df_final = df_tempo.merge(
        df_tamanho,
        on=['repositorio', 'linguagem', 'tecnologia'],
        how='inner',
    )

    # Ordena para facilitar a leitura
    df_final.sort_values(['linguagem', 'repositorio', 'tecnologia'], inplace=True)
    df_final.reset_index(drop=True, inplace=True)

    logger.info(f"Formato longo final: {len(df_final)} linhas")
    logger.info("=" * 60)

    return df_final


def validar_pareamento(df: pd.DataFrame):
    """
    Valida que o número de amostras REST é ESTRITAMENTE igual ao número
    de amostras GraphQL, tanto no total quanto agrupado por linguagem.

    Esta função serve como um sanity check para garantir que a remoção
    pareada de outliers funcionou corretamente.

    Args:
        df: DataFrame no formato longo (deve conter 'tecnologia' e 'linguagem')
    """
    logger.info("=" * 60)
    logger.info("ETAPA: Validação de Pareamento (Sanity Check)")
    logger.info("=" * 60)

    # ── Validação global ─────────────────────────────────────────────
    n_rest = len(df[df['tecnologia'] == 'REST'])
    n_graphql = len(df[df['tecnologia'] == 'GraphQL'])

    print(f"\n{'=' * 60}")
    print("  VALIDAÇÃO DE PAREAMENTO")
    print(f"{'=' * 60}")
    print(f"  Total de amostras REST:    {n_rest}")
    print(f"  Total de amostras GraphQL: {n_graphql}")

    if n_rest == n_graphql:
        print(f"  ✅ Pareamento GLOBAL OK: REST ({n_rest}) == GraphQL ({n_graphql})")
    else:
        print(f"  ❌ ERRO DE PAREAMENTO GLOBAL: REST ({n_rest}) != GraphQL ({n_graphql})")
        logger.error(
            f"Pareamento global quebrado! REST={n_rest}, GraphQL={n_graphql}. "
            "Verifique a função remover_outliers_pareado."
        )

    # ── Validação por linguagem ──────────────────────────────────────
    print(f"\n  Validação por linguagem:")
    print(f"  {'Linguagem':<20} {'REST':<8} {'GraphQL':<8} {'Status':<10}")
    print(f"  {'-' * 46}")

    todas_ok = True
    linguagens = sorted(df['linguagem'].unique())

    for linguagem in linguagens:
        n_rest_ling = len(df[(df['tecnologia'] == 'REST') & (df['linguagem'] == linguagem)])
        n_graphql_ling = len(df[(df['tecnologia'] == 'GraphQL') & (df['linguagem'] == linguagem)])

        if n_rest_ling == n_graphql_ling:
            status = "✅ OK"
        else:
            status = "❌ FALHA"
            todas_ok = False
            logger.error(
                f"Pareamento quebrado para {linguagem}: "
                f"REST={n_rest_ling}, GraphQL={n_graphql_ling}"
            )

        print(f"  {linguagem:<20} {n_rest_ling:<8} {n_graphql_ling:<8} {status:<10}")

    print(f"  {'-' * 46}")

    if todas_ok:
        print(f"  ✅ Todos os pares estão balanceados por linguagem.")
    else:
        print(f"  ❌ Existem linguagens com pareamento quebrado.")

    print(f"{'=' * 60}\n")

    # Se houver falha, emitimos um aviso forte mas não interrompemos
    if not todas_ok or n_rest != n_graphql:
        logger.warning(
            "Pareamento apresenta inconsistências. Os resultados estatísticos "
            "podem estar comprometidos."
        )


def calcular_medias_por_linguagem(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula as médias de tempo e tamanho por tecnologia e linguagem.
    Retorna um DataFrame pivotado.
    """
    medias = df.groupby(["tecnologia", "linguagem"]).agg(
        tempo_medio_ms=("tempo_ms", "mean"),
        tamanho_medio_bytes=("tamanho_bytes", "mean"),
        contagem=("tempo_ms", "count"),
    ).round(2).reset_index()

    return medias


def executar_teste_mannwhitney(
    df: pd.DataFrame, metrica: str, linguagem: str
) -> dict:
    """
    Executa o Teste de Mann-Whitney U (unilateral) para comparar
    GraphQL vs REST em uma métrica específica.

    H0: GraphQL >= REST (GraphQL não é mais rápido/menor)
    H1: GraphQL < REST (GraphQL é mais rápido/menor)

    Args:
        df: DataFrame com os dados
        metrica: Nome da coluna a ser testada ('tempo_ms' ou 'tamanho_bytes')
        linguagem: Linguagem a ser filtrada

    Returns:
        Dict com estatísticas do teste
    """
    df_rest = df[(df["tecnologia"] == "REST") & (df["linguagem"] == linguagem)][metrica]
    df_graphql = df[(df["tecnologia"] == "GraphQL") & (df["linguagem"] == linguagem)][metrica]

    if len(df_rest) < 2 or len(df_graphql) < 2:
        return {
            "linguagem": linguagem,
            "metrica": metrica,
            "n_rest": len(df_rest),
            "n_graphql": len(df_graphql),
            "u_statistic": None,
            "p_value": None,
            "significativo": False,
            "erro": "Amostra insuficiente (n < 2)",
        }

    # Teste unilateral: GraphQL < REST
    # alternative='less' testa se a distribuição de GraphQL é menor que REST
    u_stat, p_value = mannwhitneyu(
        df_graphql,
        df_rest,
        alternative="less",
    )

    significativo = p_value < NIVEL_SIGNIFICANCIA

    return {
        "linguagem": linguagem,
        "metrica": metrica,
        "n_rest": len(df_rest),
        "n_graphql": len(df_graphql),
        "u_statistic": u_stat,
        "p_value": p_value,
        "significativo": significativo,
    }


def exibir_resultados(medias: pd.DataFrame, resultados_teste: list,
                      metrica: str, unidade: str, nome_metrica: str):
    """
    Exibe os resultados formatados no console.
    """
    print(f"\n{'=' * 70}")
    print(f"  RQ: {nome_metrica}")
    print(f"{'=' * 70}")
    print(f"{'Linguagem':<15} {'REST μ':<15} {'GraphQL μ':<15} {'Diferença':<15} {'p-value':<12} {'Signif.':<10}")
    print(f"{'-' * 70}")

    for teste in resultados_teste:
        linguagem = teste["linguagem"]
        if teste["p_value"] is None:
            print(f"{linguagem:<15} {'---':<15} {'---':<15} {'---':<15} {'---':<12} {teste['erro']:<10}")
            continue

        # Busca médias
        media_rest = medias[
            (medias["tecnologia"] == "REST") &
            (medias["linguagem"] == linguagem)
        ][f"{metrica}_medio_{unidade}"].values

        media_graphql = medias[
            (medias["tecnologia"] == "GraphQL") &
            (medias["linguagem"] == linguagem)
        ][f"{metrica}_medio_{unidade}"].values

        media_rest_val = media_rest[0] if len(media_rest) > 0 else 0
        media_graphql_val = media_graphql[0] if len(media_graphql) > 0 else 0
        diferenca = media_rest_val - media_graphql_val
        diferenca_pct = (diferenca / media_rest_val * 100) if media_rest_val > 0 else 0

        p_val = teste["p_value"]
        signif = "Sim ✅" if teste["significativo"] else "Não ❌"

        print(
            f"{linguagem:<15} "
            f"{media_rest_val:<15.2f} "
            f"{media_graphql_val:<15.2f} "
            f"{diferenca:<15.2f} "
            f"{p_val:<12.6f} "
            f"{signif:<10}"
        )

    print(f"{'-' * 70}")


def salvar_resultados_md(
    df: pd.DataFrame,
    medias: pd.DataFrame,
    resultados_rq1: list,
    resultados_rq2: list,
    n_repos_antes: int,
    n_repos_removidos: int,
    caminho: str = ARQUIVO_MD,
):
    """
    Salva todos os resultados da análise em um arquivo Markdown (.md)
    para exportação e consulta offline.

    O arquivo contém:
    - Metadados da execução (data, parâmetros)
    - Resumo da remoção de outliers pareada
    - Tabela de validação de pareamento por linguagem
    - Tabelas detalhadas de RQ1 (Tempo) e RQ2 (Tamanho)
    - Conclusão sobre as hipóteses

    Args:
        df: DataFrame limpo e pareado (formato longo)
        medias: DataFrame com médias por tecnologia e linguagem
        resultados_rq1: Lista de dicts com resultados do teste para RQ1
        resultados_rq2: Lista de dicts com resultados do teste para RQ2
        n_repos_antes: Número de repositórios antes da remoção de outliers
        n_repos_removidos: Número de repositórios removidos como outliers
        caminho: Caminho do arquivo .md de saída
    """
    from datetime import datetime

    n_repos_depois = n_repos_antes - n_repos_removidos
    n_rest = len(df[df['tecnologia'] == 'REST'])
    n_graphql = len(df[df['tecnologia'] == 'GraphQL'])
    linguagens = sorted(df['linguagem'].unique())

    # ── Estatísticas de conclusão ────────────────────────────────────
    rq1_significativos = sum(1 for r in resultados_rq1 if r.get("significativo"))
    rq1_total = sum(1 for r in resultados_rq1 if r.get("p_value") is not None)
    rq2_significativos = sum(1 for r in resultados_rq2 if r.get("significativo"))
    rq2_total = sum(1 for r in resultados_rq2 if r.get("p_value") is not None)

    # ── Monta string Markdown ────────────────────────────────────────
    linhas = []
    _ = linhas.append

    # Cabeçalho
    _("# Análise Estatística — GitHub REST (v3) vs GraphQL (v4)\n")
    _(f"**Data da execução:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _(f"**Arquivo de dados:** `{ARQUIVO_CSV}`")
    _(f"**Nível de significância:** {NIVEL_SIGNIFICANCIA}")
    _("")

    # 1. Remoção de Outliers
    _("## 1. Remoção de Outliers (Pareada)")
    _("")
    _("| Indicador | Valor |")
    _("|---|---|")
    _(f"| Repositórios antes da limpeza | {n_repos_antes} |")
    _(f"| Repositórios removidos (outlier) | {n_repos_removidos} ({n_repos_removidos / n_repos_antes * 100:.1f}%) |")
    _(f"| Repositórios mantidos | {n_repos_depois} |")
    _("")
    _("> **Metodologia:** Para cada linguagem, calculou-se o IQR das 4 métricas "
      "(REST_tempo, GraphQL_tempo, REST_tamanho, GraphQL_tamanho). "
      "Se qualquer métrica de um repositório foi considerada outlier, "
      "o repositório inteiro (REST + GraphQL) foi descartado, "
      "garantindo pareamento 1:1.")
    _("")

    # 2. Validação de Pareamento
    _("## 2. Validação de Pareamento")
    _("")
    _("| Linguagem | REST | GraphQL | Status |")
    _("|---|---|---|---|")

    todas_ok = True
    for linguagem in linguagens:
        n_rest_ling = len(df[(df['tecnologia'] == 'REST') & (df['linguagem'] == linguagem)])
        n_graphql_ling = len(df[(df['tecnologia'] == 'GraphQL') & (df['linguagem'] == linguagem)])
        if n_rest_ling == n_graphql_ling:
            status = "✅ OK"
        else:
            status = "❌ FALHA"
            todas_ok = False
        _(f"| {linguagem} | {n_rest_ling} | {n_graphql_ling} | {status} |")

    _("")
    if n_rest == n_graphql:
        _("**✅ Pareamento GLOBAL OK:** REST ({}) == GraphQL ({})".format(n_rest, n_graphql))
    else:
        _("**❌ ERRO DE PAREAMENTO GLOBAL:** REST ({}) != GraphQL ({})".format(n_rest, n_graphql))
    _("")

    # 3. RQ1 — Tempo de Resposta
    _("## 3. RQ1 — Tempo de Resposta (ms)")
    _("")
    _("| Linguagem | REST μ (ms) | GraphQL μ (ms) | Diferença (ms) | Diferença (%) | p-value | U | Signif. |")
    _("|---|---|---|---|---|---|---|---|")

    for teste in resultados_rq1:
        linguagem = teste["linguagem"]
        if teste["p_value"] is None:
            _(f"| {linguagem} | --- | --- | --- | --- | --- | --- | {teste['erro']} |")
            continue

        media_rest = medias[
            (medias["tecnologia"] == "REST") & (medias["linguagem"] == linguagem)
        ]["tempo_medio_ms"].values
        media_graphql = medias[
            (medias["tecnologia"] == "GraphQL") & (medias["linguagem"] == linguagem)
        ]["tempo_medio_ms"].values

        media_rest_val = media_rest[0] if len(media_rest) > 0 else 0
        media_graphql_val = media_graphql[0] if len(media_graphql) > 0 else 0
        diferenca = media_rest_val - media_graphql_val
        diferenca_pct = (diferenca / media_rest_val * 100) if media_rest_val > 0 else 0

        p_val = teste["p_value"]
        u_val = teste["u_statistic"]
        signif = "Sim ✅" if teste["significativo"] else "Não ❌"

        _(
            f"| {linguagem} "
            f"| {media_rest_val:.2f} "
            f"| {media_graphql_val:.2f} "
            f"| {diferenca:.2f} "
            f"| {diferenca_pct:.1f}% "
            f"| {p_val:.6f} "
            f"| {u_val} "
            f"| {signif} |"
        )

    _("")

    # 4. RQ2 — Tamanho do Payload
    _("## 4. RQ2 — Tamanho do Payload (bytes)")
    _("")
    _("| Linguagem | REST μ (bytes) | GraphQL μ (bytes) | Diferença (bytes) | Diferença (%) | p-value | U | Signif. |")
    _("|---|---|---|---|---|---|---|---|")

    for teste in resultados_rq2:
        linguagem = teste["linguagem"]
        if teste["p_value"] is None:
            _(f"| {linguagem} | --- | --- | --- | --- | --- | --- | {teste['erro']} |")
            continue

        media_rest = medias[
            (medias["tecnologia"] == "REST") & (medias["linguagem"] == linguagem)
        ]["tamanho_medio_bytes"].values
        media_graphql = medias[
            (medias["tecnologia"] == "GraphQL") & (medias["linguagem"] == linguagem)
        ]["tamanho_medio_bytes"].values

        media_rest_val = media_rest[0] if len(media_rest) > 0 else 0
        media_graphql_val = media_graphql[0] if len(media_graphql) > 0 else 0
        diferenca = media_rest_val - media_graphql_val
        diferenca_pct = (diferenca / media_rest_val * 100) if media_rest_val > 0 else 0

        p_val = teste["p_value"]
        u_val = teste["u_statistic"]
        signif = "Sim ✅" if teste["significativo"] else "Não ❌"

        _(
            f"| {linguagem} "
            f"| {media_rest_val:.2f} "
            f"| {media_graphql_val:.2f} "
            f"| {diferenca:.2f} "
            f"| {diferenca_pct:.1f}% "
            f"| {p_val:.6f} "
            f"| {u_val} "
            f"| {signif} |"
        )

    _("")

    # 5. Resumo Geral
    _("## 5. Resumo Geral")
    _("")
    _("| Indicador | Valor |")
    _("|---|---|")
    _(f"| Total de amostras | {len(df)} |")
    _(f"| Amostras REST | {n_rest} |")
    _(f"| Amostras GraphQL | {n_graphql} |")
    _(f"| Linguagens | {df['linguagem'].nunique()} |")
    _(f"| Repositórios | {df['repositorio'].nunique()} |")
    _("")
    _(f"**RQ1 — Tempo:** {rq1_significativos}/{rq1_total} linguagens com diferença significativa.")
    _(f"**RQ2 — Tamanho:** {rq2_significativos}/{rq2_total} linguagens com diferença significativa.")
    _("")

    # 6. Conclusão
    _("## 6. Conclusão")
    _("")

    if rq1_significativos == rq1_total and rq1_total > 0:
        _("- ✅ **RQ1:** GraphQL é significativamente mais rápido que REST "
          "em todas as linguagens analisadas.")
    elif rq1_significativos > 0:
        _(f"- ⚠️ **RQ1:** GraphQL é mais rápido em {rq1_significativos}/{rq1_total} "
          "linguagens. Resultado misto.")
    else:
        _("- ❌ **RQ1:** Não há evidência significativa de que GraphQL "
          "seja mais rápido que REST.")

    if rq2_significativos == rq2_total and rq2_total > 0:
        _("- ✅ **RQ2:** GraphQL tem payload significativamente menor que REST "
          "em todas as linguagens analisadas.")
    elif rq2_significativos > 0:
        _(f"- ⚠️ **RQ2:** GraphQL tem payload menor em {rq2_significativos}/{rq2_total} "
          "linguagens. Resultado misto.")
    else:
        _("- ❌ **RQ2:** Não há evidência significativa de que GraphQL "
          "tenha payload menor que REST.")

    _("")
    _("---")
    _("*Relatório gerado automaticamente pelo script de análise estatística.*")

    # ── Escreve arquivo ──────────────────────────────────────────────
    conteudo = "\n".join(linhas)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

    logger.info(f"Resultados salvos em: {caminho}")


def exibir_resumo_geral(df: pd.DataFrame, resultados_rq1: list,
                        resultados_rq2: list):
    """
    Exibe um resumo geral dos resultados.
    """
    print(f"\n{'=' * 70}")
    print("  RESUMO GERAL")
    print(f"{'=' * 70}")

    # Contagem total
    print(f"\nTotal de amostras: {len(df)}")
    print(f"  REST: {len(df[df['tecnologia'] == 'REST'])}")
    print(f"  GraphQL: {len(df[df['tecnologia'] == 'GraphQL'])}")
    print(f"  Linguagens: {df['linguagem'].nunique()}")
    print(f"  Repositórios: {df['repositorio'].nunique()}")

    # RQ1
    rq1_significativos = sum(1 for r in resultados_rq1 if r.get("significativo"))
    rq1_total = sum(1 for r in resultados_rq1 if r.get("p_value") is not None)
    print(f"\nRQ1 - Tempo de Resposta:")
    print(f"  Linguagens com diferença significativa: {rq1_significativos}/{rq1_total}")

    # RQ2
    rq2_significativos = sum(1 for r in resultados_rq2 if r.get("significativo"))
    rq2_total = sum(1 for r in resultados_rq2 if r.get("p_value") is not None)
    print(f"RQ2 - Tamanho do Payload:")
    print(f"  Linguagens com diferença significativa: {rq2_significativos}/{rq2_total}")

    # Conclusão
    print(f"\n{'=' * 70}")
    print("  CONCLUSÃO")
    print(f"{'=' * 70}")

    if rq1_significativos == rq1_total and rq1_total > 0:
        print("  ✅ RQ1: GraphQL é significativamente mais rápido que REST "
              "em todas as linguagens analisadas.")
    elif rq1_significativos > 0:
        print(f"  ⚠️  RQ1: GraphQL é mais rápido em {rq1_significativos}/{rq1_total} "
              "linguagens. Resultado misto.")
    else:
        print("  ❌ RQ1: Não há evidência significativa de que GraphQL "
              "seja mais rápido que REST.")

    if rq2_significativos == rq2_total and rq2_total > 0:
        print("  ✅ RQ2: GraphQL tem payload significativamente menor que REST "
              "em todas as linguagens analisadas.")
    elif rq2_significativos > 0:
        print(f"  ⚠️  RQ2: GraphQL tem payload menor em {rq2_significativos}/{rq2_total} "
              "linguagens. Resultado misto.")
    else:
        print("  ❌ RQ2: Não há evidência significativa de que GraphQL "
              "tenha payload menor que REST.")

    print(f"{'=' * 70}\n")


# ──────────────────────────────────────────────────────────────────────
# Pipeline Principal
# ──────────────────────────────────────────────────────────────────────

def main():
    """Função principal do script de análise."""
    logger.info("=" * 60)
    logger.info("Iniciando Análise Estatística — REST vs GraphQL")
    logger.info("=" * 60)

    # 1. Carrega dados
    df = carregar_dados(ARQUIVO_CSV)

    # 2. Remove outliers de forma PAREADA (NOVA METODOLOGIA)
    #    Antes: remover_outliers_iqr() independente para REST e GraphQL
    #    Agora: remover_outliers_pareado() trata o repositório como unidade
    df_limpo = remover_outliers_pareado(df)

    # 3. Valida o pareamento (Sanity Check)
    #    Garante que REST == GraphQL tanto global quanto por linguagem
    validar_pareamento(df_limpo)

    # 4. Calcula médias
    medias = calcular_medias_por_linguagem(df_limpo)
    logger.info("\nMédias calculadas por tecnologia e linguagem.")

    # 5. Executa testes para cada linguagem
    linguagens = df_limpo["linguagem"].unique()

    # RQ1: Tempo de Resposta
    logger.info("\nExecutando Teste de Mann-Whitney para RQ1 (tempo)...")
    resultados_rq1 = []
    for linguagem in linguagens:
        resultado = executar_teste_mannwhitney(df_limpo, "tempo_ms", linguagem)
        resultados_rq1.append(resultado)
        logger.info(
            f"  {linguagem}: U={resultado['u_statistic']}, "
            f"p={resultado['p_value']:.6f}, "
            f"significativo={resultado['significativo']}"
        )

    # RQ2: Tamanho do Payload
    logger.info("\nExecutando Teste de Mann-Whitney para RQ2 (tamanho)...")
    resultados_rq2 = []
    for linguagem in linguagens:
        resultado = executar_teste_mannwhitney(df_limpo, "tamanho_bytes", linguagem)
        resultados_rq2.append(resultado)
        logger.info(
            f"  {linguagem}: U={resultado['u_statistic']}, "
            f"p={resultado['p_value']:.6f}, "
            f"significativo={resultado['significativo']}"
        )

    # 6. Exibe resultados formatados
    exibir_resultados(
        medias, resultados_rq1,
        metrica="tempo", unidade="ms", nome_metrica="RQ1: Tempo de Resposta (ms)"
    )
    exibir_resultados(
        medias, resultados_rq2,
        metrica="tamanho", unidade="bytes",
        nome_metrica="RQ2: Tamanho do Payload (bytes)"
    )

    # 7. Exibe resumo geral
    exibir_resumo_geral(df_limpo, resultados_rq1, resultados_rq2)

    # 8. Salva resultados em arquivo Markdown
    #    (Obtém n_repos_antes e n_repos_removidos do escopo da função
    #     remover_outliers_pareado — precisamos capturá-los. Como a função
    #     já foi chamada, recalculamos a partir do df original.)
    n_repos_antes = df['repositorio'].nunique()
    n_repos_depois = df_limpo['repositorio'].nunique()
    n_repos_removidos = n_repos_antes - n_repos_depois

    salvar_resultados_md(
        df=df_limpo,
        medias=medias,
        resultados_rq1=resultados_rq1,
        resultados_rq2=resultados_rq2,
        n_repos_antes=n_repos_antes,
        n_repos_removidos=n_repos_removidos,
    )

    logger.info("Análise concluída com sucesso!")


if __name__ == "__main__":
    main()