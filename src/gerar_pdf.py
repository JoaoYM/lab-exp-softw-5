#!/usr/bin/env python3
"""
Conversor de Relatório Markdown para PDF com Aparência Acadêmica
=================================================================
Laboratório 05 — Comparação de eficiência entre APIs do GitHub.

Este script:
1. Lê o arquivo docs/relatorio_experimento.md
2. Converte o Markdown para HTML usando a biblioteca 'markdown'
3. Aplica CSS acadêmico avançado (capa, fontes serifadas, margens A4,
   tabelas com bordas pretas, imagens dimensionadas, quebras de página,
   numeração de páginas, hifenização, recuo de parágrafos)
4. Gera o PDF final usando a biblioteca 'weasyprint'

Uso:
    python3 src/gerar_pdf.py

Requer (instalar via WSL):
    pip3 install markdown weasyprint

Saída:
    docs/relatorio_experimento.pdf
"""

import sys
import logging
from pathlib import Path

import markdown
from weasyprint import HTML

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
ARQUIVO_MD = BASE_DIR / "docs" / "relatorio_experimento.md"
ARQUIVO_PDF = BASE_DIR / "docs" / "relatorio_experimento.pdf"
PASTA_ASSETS = BASE_DIR / "assets"

# ──────────────────────────────────────────────────────────────────────
# CSS Acadêmico Avançado
# ──────────────────────────────────────────────────────────────────────
CSS_ACADEMICO = """
/* ── Configuração da Página A4 ────────────────────────────────── */
@page {
    size: A4;
    margin: 2.5cm 2.5cm 2.5cm 2.5cm;

    @bottom-right {
        content: counter(page);
        font-family: "Times New Roman", Georgia, serif;
        font-size: 10pt;
        color: #555555;
    }

    @top-center {
        content: "REST (v3) vs GraphQL (v4) — Relatório Experimental";
        font-family: "Times New Roman", Georgia, serif;
        font-size: 8pt;
        color: #999999;
        font-style: italic;
    }
}

/* --- Formatação da Capa Acadêmica (Estilo ABNT) --- */
.capa {
    text-align: center;
    page-break-after: always;
    position: relative; /* Cria o contexto de ancoragem para o rodapé */
    height: 90vh; /* Altura segura para a primeira página */
    font-family: "Times New Roman", Times, serif;
}

.capa .cabecalho {
    font-size: 14pt;
    font-weight: bold;
    line-height: 1.5;
    margin-top: 1cm;
}

.capa .titulo-container {
    /* Empurra o título para o centro ótico da folha (aprox. 40% da altura) */
    position: absolute;
    top: 40%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
}

.capa h1 {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 10px;
    border: none;
}

.capa h2 {
    font-size: 14pt;
    font-weight: normal;
    color: #333;
}

.capa .autor {
    /* Posicionado um pouco abaixo do centro */
    position: absolute;
    top: 60%;
    width: 100%;
    font-size: 14pt;
    font-weight: bold;
}

.capa .rodape {
    /* Ancora a cidade e o ano rigorosamente no final da página */
    position: absolute;
    bottom: 0;
    width: 100%;
    font-size: 12pt;
    font-weight: bold;
    line-height: 1.5;
}

/* ── Quebras de Página ───────────────────────────────────────── */
h1 {
    page-break-before: always;
    page-break-after: avoid;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    page-break-before: always;
    page-break-after: avoid;
}

h2:first-of-type {
    page-break-before: avoid;
}

h3, h4, h5 {
    page-break-after: avoid;
}

table, figure, img, pre, blockquote {
    page-break-inside: avoid;
}

/* ── Tipografia Geral ──────────────────────────────────────────── */
body {
    font-family: "Times New Roman", Georgia, "Palatino Linotype", "Book Antiqua", serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #1a1a1a;
    text-align: justify;
    orphans: 3;
    widows: 3;
}

/* ── Parágrafos — justificados + hifenização + recuo ──────────── */
p {
    text-align: justify;
    hyphens: auto;
    text-indent: 1.5em;
    margin-top: 0;
    margin-bottom: 0.3em;
}

/* Sem recuo após títulos */
h1 + p, h2 + p, h3 + p, h4 + p {
    text-indent: 0;
}

/* ── Títulos ───────────────────────────────────────────────────── */
h1 {
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    margin-top: 0;
    margin-bottom: 0.6cm;
    color: #000000;
    letter-spacing: 0.5pt;
}

h2 {
    font-size: 15pt;
    font-weight: bold;
    margin-top: 1cm;
    margin-bottom: 0.4cm;
    color: #1a1a1a;
    border-bottom: 1.5px solid #aaaaaa;
    padding-bottom: 4pt;
}

h3 {
    font-size: 13pt;
    font-weight: bold;
    margin-top: 0.6cm;
    margin-bottom: 0.3cm;
    color: #333333;
}

h4 {
    font-size: 12pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 0.4cm;
    margin-bottom: 0.2cm;
    color: #444444;
}

/* ── Tabelas — bordas pretas, padding 8px ─────────────────────── */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.4cm;
    margin-bottom: 0.4cm;
    font-size: 10pt;
    page-break-inside: avoid;
}

th {
    background-color: #f0f0f0;
    font-weight: bold;
    padding: 8px;
    border: 1px solid #000000;
    text-align: left;
    vertical-align: middle;
}

td {
    padding: 8px;
    border: 1px solid #000000;
    vertical-align: middle;
    text-align: left;
}

tr:nth-child(even) {
    background-color: #fafafa;
}

/* ── Imagens — NUNCA cortar, max-height 85vh ──────────────────── */
img {
    max-width: 100%;
    max-height: 85vh;
    object-fit: contain;
    display: block;
    margin: 0.5cm auto;
    page-break-inside: avoid;
    border: none;
}

/* ── Blocos de Citação ─────────────────────────────────────────── */
blockquote {
    margin: 0.4cm 0;
    padding: 8pt 12pt 8pt 15pt;
    border-left: 3px solid #666666;
    background-color: #f9f9f9;
    font-style: italic;
    font-size: 11pt;
    color: #444444;
    page-break-inside: avoid;
}

/* ── Código ────────────────────────────────────────────────────── */
code {
    font-family: "Courier New", Courier, "Lucida Console", monospace;
    font-size: 10pt;
    background-color: #f4f4f4;
    padding: 1pt 4pt;
    border-radius: 2pt;
}

pre {
    font-family: "Courier New", Courier, "Lucida Console", monospace;
    font-size: 9pt;
    background-color: #f8f8f8;
    border: 1px solid #dddddd;
    padding: 8pt;
    margin: 0.3cm 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    page-break-inside: avoid;
    line-height: 1.3;
}

/* ── Listas ────────────────────────────────────────────────────── */
ul, ol {
    margin-top: 0.2cm;
    margin-bottom: 0.2cm;
    padding-left: 1cm;
}

li {
    margin-bottom: 3pt;
    text-align: justify;
}

/* ── Linha Horizontal ──────────────────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid #cccccc;
    margin: 0.5cm 0;
}

/* ── Ênfase ────────────────────────────────────────────────────── */
strong {
    font-weight: bold;
    color: #000000;
}

em {
    font-style: italic;
}

/* ── Legendas de Imagens / Figuras ─────────────────────────────── */
em:only-child, p > em:only-child {
    display: block;
    text-align: center;
    font-size: 10pt;
    color: #666666;
    margin-top: -0.3cm;
    margin-bottom: 0.4cm;
    font-style: italic;
}
"""


# ──────────────────────────────────────────────────────────────────────
# Funções
# ──────────────────────────────────────────────────────────────────────

def converter_md_para_html(caminho_md: str) -> str:
    """
    Lê o arquivo Markdown e converte para HTML.

    Args:
        caminho_md: Caminho do arquivo .md

    Returns:
        String HTML completa (com doctype, html, head, body)
    """
    if not Path(caminho_md).exists():
        logger.error(f"Arquivo {caminho_md} não encontrado.")
        sys.exit(1)

    with open(caminho_md, "r", encoding="utf-8") as f:
        texto_md = f.read()

    logger.info(f"Markdown lido: {len(texto_md)} caracteres de {caminho_md}")

    # Converte Markdown para HTML com extensões
    html_body = markdown.markdown(
        texto_md,
        extensions=[
            "tables",        # Tabelas
            "fenced_code",   # Blocos de código com ```
            "attr_list",     # Atributos em elementos
            "def_list",      # Listas de definição
            "footnotes",     # Notas de rodapé
            "md_in_html",    # Markdown dentro de HTML
        ],
    )

    # Monta documento HTML completo
    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Experimental — REST vs GraphQL</title>
    <style>
{CSS_ACADEMICO}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    logger.info("Markdown convertido para HTML com sucesso.")
    return html_completo


def gerar_pdf(html_content: str, caminho_pdf: str):
    """
    Gera o PDF a partir do conteúdo HTML usando WeasyPrint.

    Args:
        html_content: String HTML completa
        caminho_pdf: Caminho de saída do arquivo .pdf
    """
    logger.info(f"Gerando PDF: {caminho_pdf}...")

    try:
        # base_url aponta para a raiz do projeto para resolução de imagens
        caminho_base = BASE_DIR
        HTML(string=html_content, base_url=str(caminho_base)).write_pdf(caminho_pdf)
        logger.info(f"PDF gerado com sucesso: {caminho_pdf}")
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        sys.exit(1)


def main():
    """Função principal do conversor."""
    logger.info("=" * 60)
    logger.info("Conversor Markdown → PDF — Relatório Acadêmico")
    logger.info("=" * 60)

    # Garante que a pasta docs existe
    ARQUIVO_PDF.parent.mkdir(parents=True, exist_ok=True)

    # 1. Converte Markdown para HTML
    html = converter_md_para_html(ARQUIVO_MD)

    # 2. Gera PDF com base_url para resolução de imagens locais
    gerar_pdf(html, ARQUIVO_PDF)

    logger.info("Conversão concluída com sucesso!")


if __name__ == "__main__":
    main()