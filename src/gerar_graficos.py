#!/usr/bin/env python3
"""
Geração de Gráficos Estáticos e Diagrama Metodológico
======================================================
Laboratório 05 — Comparação de eficiência entre APIs do GitHub.

Este script:
1. Lê o arquivo data/resultados.csv
2. Gera 4 gráficos acadêmicos de alto contraste (300 DPI):
   - assets/chart_tempo.png      : Barras — Tempo médio (ms) por linguagem
   - assets/chart_tamanho.png    : Barras — Tamanho médio (bytes) por linguagem
   - assets/chart_boxplot.png    : Boxplot — Distribuição do tempo de resposta
   - assets/chart_scatter.png    : Dispersão — Tamanho (X) vs Tempo (Y)
3. Gera 1 diagrama do pipeline metodológico (Graphviz):
   - assets/diagrama_metodologia.png

Uso:
    python src/gerar_graficos.py

Requer:
    pip install pandas matplotlib seaborn numpy graphviz
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# ──────────────────────────────────────────────────────────────────────
# Configuração
# ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Caminhos relativos à nova estrutura de pastas
BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_CSV = BASE_DIR / "data" / "resultados.csv"
PASTA_ASSETS = BASE_DIR / "assets"

ARQUIVOS_SAIDA = {
    'tempo': PASTA_ASSETS / 'chart_tempo.png',
    'tamanho': PASTA_ASSETS / 'chart_tamanho.png',
    'boxplot': PASTA_ASSETS / 'chart_boxplot.png',
    'scatter': PASTA_ASSETS / 'chart_scatter.png',
    'diagrama': PASTA_ASSETS / 'diagrama_metodologia.png',
}

# Paleta de alto contraste (acessível, colorblind-friendly)
COR_REST = '#E74C3C'      # Vermelho forte
COR_GRAPHQL = '#2E86C1'   # Azul forte
COR_REST_CLARO = '#F1948A'
COR_GRAPHQL_CLARO = '#85C1E9'

# ──────────────────────────────────────────────────────────────────────
# Configuração Seaborn / Matplotlib
# ──────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
plt.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'font.family': 'DejaVu Sans',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': '#333333',
    'axes.linewidth': 0.8,
    'grid.color': '#cccccc',
    'grid.alpha': 0.4,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '#999999',
})


# ──────────────────────────────────────────────────────────────────────
# Funções de Carregamento
# ──────────────────────────────────────────────────────────────────────

def carregar_dados(caminho: str) -> pd.DataFrame:
    if not Path(caminho).exists():
        logger.error(f"Arquivo {caminho} não encontrado.")
        sys.exit(1)
    df = pd.read_csv(caminho)
    logger.info(f"Dados carregados: {len(df)} linhas de {caminho}")
    return df


def calcular_medias_com_erro(df: pd.DataFrame) -> dict:
    linguagens = sorted(df['linguagem'].unique())
    resultado = {
        'linguagens': linguagens,
        'tempo': {'REST': [], 'GraphQL': []},
        'tempo_std': {'REST': [], 'GraphQL': []},
        'tamanho': {'REST': [], 'GraphQL': []},
        'tamanho_std': {'REST': [], 'GraphQL': []},
    }
    for ling in linguagens:
        for tec in ['REST', 'GraphQL']:
            subset = df[(df['linguagem'] == ling) & (df['tecnologia'] == tec)]
            t_vals = subset['tempo_ms'].values
            sz_vals = subset['tamanho_bytes'].values
            resultado['tempo'][tec].append(np.mean(t_vals))
            resultado['tempo_std'][tec].append(np.std(t_vals, ddof=1) if len(t_vals) > 1 else 0)
            resultado['tamanho'][tec].append(np.mean(sz_vals))
            resultado['tamanho_std'][tec].append(np.std(sz_vals, ddof=1) if len(sz_vals) > 1 else 0)
    return resultado


# ──────────────────────────────────────────────────────────────────────
# Gráfico 1: Barras — Tempo Médio
# ──────────────────────────────────────────────────────────────────────

def gerar_barras_tempo(dados: dict, arquivo: str):
    linguagens = dados['linguagens']
    x = np.arange(len(linguagens))
    largura = 0.35

    fig, ax = plt.subplots(figsize=(10, 5.5))

    v_rest = dados['tempo']['REST']
    v_gl = dados['tempo']['GraphQL']
    e_rest = dados['tempo_std']['REST']
    e_gl = dados['tempo_std']['GraphQL']

    b1 = ax.bar(x - largura/2, v_rest, largura, label='REST (v3)',
                color=COR_REST, edgecolor='white', linewidth=0.5,
                yerr=e_rest, capsize=4, error_kw={'elinewidth': 1.5, 'ecolor': 'dimgray'})
    b2 = ax.bar(x + largura/2, v_gl, largura, label='GraphQL (v4)',
                color=COR_GRAPHQL, edgecolor='white', linewidth=0.5,
                yerr=e_gl, capsize=4, error_kw={'elinewidth': 1.5, 'ecolor': 'dimgray'})

    ax.set_xlabel('Linguagem de Programação', fontweight='bold')
    ax.set_ylabel('Tempo Médio de Resposta (ms)', fontweight='bold')
    ax.set_title('RQ1: Tempo Médio de Resposta — REST vs GraphQL', fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(linguagens)
    ax.legend(loc='upper left', framealpha=0.9, edgecolor='#999999')

    y_max = max(max(v + e for v, e in zip(v_rest, e_rest)),
                max(v + e for v, e in zip(v_gl, e_gl)))
    ax.set_ylim(0, y_max * 1.18)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    ax.grid(axis='x', visible=False)

    for bar in b1:
        h = bar.get_height()
        ax.annotate(f'{h:.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 6), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=COR_REST, fontweight='bold')
    for bar in b2:
        h = bar.get_height()
        ax.annotate(f'{h:.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 6), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=COR_GRAPHQL, fontweight='bold')

    plt.tight_layout()
    fig.savefig(arquivo, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"Gráfico salvo: {arquivo}")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────
# Gráfico 2: Barras — Tamanho Médio
# ──────────────────────────────────────────────────────────────────────

def gerar_barras_tamanho(dados: dict, arquivo: str):
    linguagens = dados['linguagens']
    x = np.arange(len(linguagens))
    largura = 0.35

    fig, ax = plt.subplots(figsize=(10, 5.5))

    v_rest = dados['tamanho']['REST']
    v_gl = dados['tamanho']['GraphQL']
    e_rest = dados['tamanho_std']['REST']
    e_gl = dados['tamanho_std']['GraphQL']

    b1 = ax.bar(x - largura/2, v_rest, largura, label='REST (v3)',
                color=COR_REST, edgecolor='white', linewidth=0.5,
                yerr=e_rest, capsize=4, error_kw={'elinewidth': 1.5, 'ecolor': 'dimgray'})
    b2 = ax.bar(x + largura/2, v_gl, largura, label='GraphQL (v4)',
                color=COR_GRAPHQL, edgecolor='white', linewidth=0.5,
                yerr=e_gl, capsize=4, error_kw={'elinewidth': 1.5, 'ecolor': 'dimgray'})

    ax.set_xlabel('Linguagem de Programação', fontweight='bold')
    ax.set_ylabel('Tamanho Médio do Payload (bytes)', fontweight='bold')
    ax.set_title('RQ2: Tamanho Médio do Payload — REST vs GraphQL', fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(linguagens)
    ax.legend(loc='upper left', framealpha=0.9, edgecolor='#999999')

    y_max = max(max(v + e for v, e in zip(v_rest, e_rest)),
                max(v + e for v, e in zip(v_gl, e_gl)))
    ax.set_ylim(0, y_max * 1.18)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    ax.grid(axis='x', visible=False)

    for bar in b1:
        h = bar.get_height()
        ax.annotate(f'{h:.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 6), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=COR_REST, fontweight='bold')
    for bar in b2:
        h = bar.get_height()
        ax.annotate(f'{h:.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 6), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, color=COR_GRAPHQL, fontweight='bold')

    plt.tight_layout()
    fig.savefig(arquivo, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"Gráfico salvo: {arquivo}")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────
# Gráfico 3: Boxplot — Distribuição do Tempo
# ──────────────────────────────────────────────────────────────────────

def gerar_boxplot_tempo(df: pd.DataFrame, arquivo: str):
    fig, ax = plt.subplots(figsize=(10, 5.5))

    dados_plot = []
    labels = []
    cores = []
    linguagens = sorted(df['linguagem'].unique())

    for ling in linguagens:
        for tec, cor in [('REST', COR_REST), ('GraphQL', COR_GRAPHQL)]:
            vals = df[(df['linguagem'] == ling) & (df['tecnologia'] == tec)]['tempo_ms'].values
            if len(vals) > 0:
                dados_plot.append(vals)
                labels.append(f'{ling}\n{tec}')
                cores.append(cor)

    bp = ax.boxplot(dados_plot, patch_artist=True, widths=0.6,
                    medianprops={'color': 'black', 'linewidth': 2},
                    flierprops={'marker': 'o', 'markerfacecolor': 'red', 'markersize': 6, 'alpha': 0.6})

    for patch, color in zip(bp['boxes'], cores):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor('black')
        patch.set_linewidth(1.2)

    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel('Tempo de Resposta (ms)', fontweight='bold')
    ax.set_title('Distribuição do Tempo de Resposta por Linguagem e Tecnologia',
                 fontweight='bold', pad=12)
    ax.grid(axis='y', alpha=0.3)

    for i, dados in enumerate(dados_plot):
        media = np.mean(dados)
        ax.plot(i + 1, media, 'D', color='yellow', markersize=8,
                markeredgecolor='black', markeredgewidth=1.5, zorder=5)

    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor=COR_REST, alpha=0.7, label='REST (v3)'),
        Patch(facecolor=COR_GRAPHQL, alpha=0.7, label='GraphQL (v4)'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='yellow',
               markersize=8, markeredgecolor='black', label='Média'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9, edgecolor='#999999')

    plt.tight_layout()
    fig.savefig(arquivo, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"Boxplot salvo: {arquivo}")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────
# Gráfico 4: Dispersão — Tamanho vs Tempo
# ──────────────────────────────────────────────────────────────────────

def gerar_scatter(df: pd.DataFrame, arquivo: str):
    fig, ax = plt.subplots(figsize=(10, 6))

    rest = df[df['tecnologia'] == 'REST']
    graphql = df[df['tecnologia'] == 'GraphQL']

    ax.scatter(rest['tamanho_bytes'], rest['tempo_ms'],
               c=COR_REST, label='REST (v3)', alpha=0.8,
               edgecolors='black', linewidth=0.5, s=80, zorder=5)
    ax.scatter(graphql['tamanho_bytes'], graphql['tempo_ms'],
               c=COR_GRAPHQL, label='GraphQL (v4)', alpha=0.8,
               edgecolors='black', linewidth=0.5, s=80, zorder=5)

    ax.set_xlabel('Tamanho do Payload (bytes)', fontweight='bold')
    ax.set_ylabel('Tempo de Resposta (ms)', fontweight='bold')
    ax.set_title('Dispersão: Tamanho do Payload vs Tempo de Resposta',
                 fontweight='bold', pad=12)
    ax.legend(loc='upper left', framealpha=0.9, edgecolor='#999999')
    ax.grid(alpha=0.3)

    ax.xaxis.set_major_formatter(plt.FuncFormatter(
        lambda v, _: f'{v/1024:.0f} KB' if v < 1024*1024 else f'{v/(1024*1024):.1f} MB'
    ))

    plt.tight_layout()
    fig.savefig(arquivo, dpi=300, bbox_inches='tight', facecolor='white')
    logger.info(f"Scatter salvo: {arquivo}")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────
# Diagrama 5: Fluxograma da Metodologia (Graphviz)
# ──────────────────────────────────────────────────────────────────────

def gerar_diagrama_metodologia(arquivo: str):
    """
    Gera o diagrama do pipeline metodológico usando Graphviz.
    size='8,10' com ratio='compress' garante que o diagrama
    caiba em uma página A4 sem cortes.
    """
    try:
        import graphviz
    except ImportError:
        logger.warning("graphviz não instalado. Pulando diagrama.")
        logger.warning("Instale com: pip install graphviz")
        logger.warning("E também o Graphviz binário: sudo apt install graphviz (WSL)")
        return

    dot = graphviz.Digraph(
        name='metodologia',
        format='png',
        engine='dot',
    )
    dot.attr(
        rankdir='TB',
        size='8,10',
        ratio='compress',
        dpi='200',
        fontname='DejaVu Sans',
        fontsize='11',
        bgcolor='white',
        label='Pipeline Metodológico do Experimento',
        labelloc='t',
        labeljust='c',
        pad='0.5',
    )
    dot.attr('node',
             shape='box',
             style='filled,rounded',
             fontname='DejaVu Sans',
             fontsize='10',
             fillcolor='#EBF5FB',
             color='#2E86C1',
             penwidth='2')

    dot.attr('edge',
             fontname='DejaVu Sans',
             fontsize='9',
             color='#555555')

    dot.node('extracao', '1. Extração de Dados\n(mineracao.py)\nREST + GraphQL pareado',
             fillcolor='#D4E6F1', color='#2166AC')
    dot.node('filtragem', '2. Filtragem\nRemoção de bots\nRemoção de mirrors',
             fillcolor='#D5F5E3', color='#27AE60')
    dot.node('separacao', '3. Separação\nREST (v3) vs GraphQL (v4)\nMesmo repositório, 2 medições',
             fillcolor='#FDEBD0', color='#E67E22')
    dot.node('sanitizacao', '4. Sanitização IQR Pareada\nPivot por repositório\nIQR em 4 métricas\nSe outlier → descarta par',
             fillcolor='#FADBD8', color='#E74C3C')
    dot.node('teste', '5. Teste Estatístico\nMann-Whitney U (unilateral)\nH₀: GraphQL ≥ REST\nH₁: GraphQL < REST\nα = 0.05',
             fillcolor='#E8DAEF', color='#8E44AD')
    dot.node('conclusao', '6. Conclusão\nRQ1: Tempo\nRQ2: Tamanho',
             fillcolor='#F9E79F', color='#B7950B')

    dot.edge('extracao', 'filtragem', label='58 linhas brutas')
    dot.edge('filtragem', 'separacao', label='29 repositórios')
    dot.edge('separacao', 'sanitizacao', label='29 pares REST/GL')
    dot.edge('sanitizacao', 'teste', label='21 pares válidos')
    dot.edge('teste', 'conclusao', label='p-value < 0.05?')

    try:
        dot.render(filename=str(arquivo).replace('.png', ''), cleanup=True)
        logger.info(f"Diagrama salvo: {arquivo}")
    except Exception as e:
        logger.error(f"Erro ao gerar diagrama Graphviz: {e}")
        logger.error("Certifique-se de que o Graphviz binário está instalado.")
        logger.error("WSL: sudo apt install graphviz")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Geração de Gráficos e Diagrama — REST vs GraphQL")
    logger.info("=" * 60)

    # Garante que a pasta assets existe
    PASTA_ASSETS.mkdir(parents=True, exist_ok=True)

    df = carregar_dados(ARQUIVO_CSV)
    dados = calcular_medias_com_erro(df)
    logger.info(f"Médias calculadas para {len(dados['linguagens'])} linguagens.")

    gerar_barras_tempo(dados, ARQUIVOS_SAIDA['tempo'])
    gerar_barras_tamanho(dados, ARQUIVOS_SAIDA['tamanho'])
    gerar_boxplot_tempo(df, ARQUIVOS_SAIDA['boxplot'])
    gerar_scatter(df, ARQUIVOS_SAIDA['scatter'])
    gerar_diagrama_metodologia(ARQUIVOS_SAIDA['diagrama'])

    logger.info("=" * 60)
    logger.info("Geração concluída com sucesso!")
    logger.info(f"Arquivos em: {PASTA_ASSETS}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()