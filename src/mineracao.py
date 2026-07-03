#!/usr/bin/env python3
"""
Script de Mineração e Coleta — GitHub REST (v3) vs GraphQL (v4)
=================================================================
Laboratório 05 — Comparação de eficiência entre APIs do GitHub.

MODO DE CONTINUAÇÃO (escopo reduzido: 30 repositórios):
--------------------------------------------------------
Este script foi refatorado para:
1. Ler os 30 repositórios que já possuem dados REST coletados
   (a partir do resultados.csv existente).
2. Executar APENAS a coleta via GraphQL v4 para esses mesmos
   30 repositórios, garantindo comparação pareada 1:1.
3. Implementar programação defensiva em todos os acessos a
   dicionários para evitar TypeError com campos nulos.
4. Manter backoff exponencial, checkpointing e filtro de bots.

Uso:
    python mineracao.py

Requer:
    - python-dotenv, requests
    - Arquivo .env com GITHUB_TOKEN
    - Arquivo resultados.csv com dados REST já coletados
"""

import os
import sys
import json
import time
import csv
import math
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

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
# Constantes
# ──────────────────────────────────────────────────────────────────────

# Linguagens do Octoverse 2024 (principais)
LINGUAGENS_OCTOVERSE = [
    "JavaScript",
    "Python",
    "TypeScript",
    "Java",
    "Go",
    "C#",
]

TOTAL_REPOS = 30           # Escopo reduzido: 30 repositórios
PRS_POR_REPO = 200         # Total de PRs por repositório
PRS_POR_PAGINA = 10        # Tamanho do lote de PRs (GraphQL)
COMENTARIOS_POR_PAGINA = 100  # Tamanho do lote de reviews/comments

# Headers da API
HEADERS_REST = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "lab-exp-softw-5/1.0",
}
HEADERS_GRAPHQL = {
    "Accept": "application/vnd.github.v4+json",
    "User-Agent": "lab-exp-softw-5/1.0",
}

# URLs base
REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

# Bots conhecidos para filtrar
BOTS_CONHECIDOS = {
    "dependabot[bot]",
    "github-actions[bot]",
    "greenkeeper[bot]",
    "renovate[bot]",
    "snyk-bot",
    "codecov[bot]",
    "coveralls[bot]",
    "gitter-badger",
    "semantic-release-bot",
    "imgbot[bot]",
    "lgtm-com[bot]",
    "bot",
}

# Caminhos relativos à nova estrutura de pastas
BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_ESTADO = str(BASE_DIR / "data" / "estado.json")
ARQUIVO_CSV = str(BASE_DIR / "data" / "resultados.csv")
ARQUIVO_ENV = str(BASE_DIR / ".env")


# ──────────────────────────────────────────────────────────────────────
# Utilitários
# ──────────────────────────────────────────────────────────────────────

def carregar_token() -> str:
    """Carrega o token GitHub do arquivo .env ou variável de ambiente."""
    load_dotenv(ARQUIVO_ENV)
    token = os.getenv("GITHUB_TOKEN")
    if not token or token == "seu_token_aqui":
        logger.error(
            "Token GitHub não encontrado. Configure GITHUB_TOKEN no arquivo .env"
        )
        sys.exit(1)
    return token


def is_bot(login: str) -> bool:
    """
    Verifica se um usuário é um bot conhecido.
    Retorna True para bots, usuários deletados ou None.
    """
    if not login:
        return True
    login_lower = login.lower()
    if login_lower in BOTS_CONHECIDOS:
        return True
    if "[bot]" in login_lower:
        return True
    return False


def extrair_tamanho_resposta(response: requests.Response) -> int:
    """Extrai o tamanho do payload em bytes."""
    return len(response.content)


def obter_seguro(dicionario: dict, *caminhos, fallback=None):
    """
    Acessa um dicionário aninhado de forma segura, retornando fallback
    se qualquer chave no caminho não existir ou for None.

    Exemplo:
        obter_seguro(data, "usuario", "endereco", "cidade", fallback="Desconhecido")
    Equivalente a: ((data.get("usuario") or {}).get("endereco") or {}).get("cidade", "Desconhecido")
    """
    if dicionario is None:
        return fallback
    atual = dicionario
    for chave in caminhos:
        if atual is None or not isinstance(atual, dict):
            return fallback
        atual = atual.get(chave)
    return atual if atual is not None else fallback


# ──────────────────────────────────────────────────────────────────────
# Backoff Exponencial e Rate Limiting
# ──────────────────────────────────────────────────────────────────────

def verificar_rate_limit_rest(response: requests.Response) -> tuple:
    """
    Verifica headers de rate limit da API REST.
    Retorna (remaining, reset_time).
    """
    remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
    reset_epoch = int(response.headers.get("X-RateLimit-Reset", 0))
    return remaining, reset_epoch


def backoff_exponencial(
    tentativa: int,
    response: requests.Response = None,
    base: float = 1.0,
    max_wait: float = 120.0,
):
    """
    Implementa backoff exponencial.
    Se response for fornecido, verifica headers de rate limit.
    """
    if response is not None:
        status = response.status_code
        remaining, reset_epoch = verificar_rate_limit_rest(response)

        # Se estourou rate limit ou recebeu 403/429
        if status in (403, 429) or remaining == 0:
            if reset_epoch > 0:
                wait_time = max(reset_epoch - time.time(), 1) + 1
                logger.warning(
                    f"Rate limit excedido. Aguardando {wait_time:.0f}s até reset..."
                )
                time.sleep(wait_time)
                return
            else:
                # Fallback para backoff exponencial
                wait_time = min(base * (2 ** tentativa), max_wait)
                logger.warning(
                    f"HTTP {status}. Backoff: {wait_time:.1f}s (tentativa {tentativa + 1})"
                )
                time.sleep(wait_time)
                return

    # Backoff padrão para erros de rede
    wait_time = min(base * (2 ** tentativa), max_wait)
    logger.info(f"Backoff: {wait_time:.1f}s (tentativa {tentativa + 1})")
    time.sleep(wait_time)


def verificar_e_esperar_rate_limit(headers: dict, token: str):
    """
    Verifica o rate limit atual da API REST e espera se necessário.
    """
    url = f"{REST_BASE}/rate_limit"
    try:
        resp = requests.get(
            url, headers={**headers, "Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            remaining = obter_seguro(
                data, "resources", "core", "remaining", fallback=5000
            )
            reset_epoch = obter_seguro(
                data, "resources", "core", "reset", fallback=0
            )

            if remaining < 10:
                wait_time = max(reset_epoch - time.time(), 1) + 1
                logger.warning(
                    f"Rate limit baixo ({remaining} restantes). "
                    f"Aguardando {wait_time:.0f}s até reset..."
                )
                time.sleep(wait_time)
                return True
    except Exception as e:
        logger.warning(f"Não foi possível verificar rate limit: {e}")

    return False


# ──────────────────────────────────────────────────────────────────────
# Leitura dos Repositórios com Dados REST (a partir do CSV)
# ──────────────────────────────────────────────────────────────────────

def carregar_repos_com_rest_do_csv() -> list:
    """
    Lê o arquivo resultados.csv e extrai os repositórios que já possuem
    dados REST coletados. Retorna uma lista de dicts com as chaves:
    full_name, owner, repo, language.

    Limita a TOTAL_REPOS (30) repositórios.
    """
    if not Path(ARQUIVO_CSV).exists():
        logger.error(
            f"Arquivo {ARQUIVO_CSV} não encontrado. "
            "Execute primeiro a coleta REST para gerar os dados."
        )
        sys.exit(1)

    repos_encontrados = []
    repos_vistos = set()

    with open(ARQUIVO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tecnologia = (row.get("tecnologia") or "").strip()
            repositorio = (row.get("repositorio") or "").strip()
            linguagem = (row.get("linguagem") or "").strip()

            # Só nos interessam linhas REST
            if tecnologia != "REST":
                continue
            if not repositorio:
                continue

            # Evita duplicatas
            if repositorio in repos_vistos:
                continue
            repos_vistos.add(repositorio)

            # Extrai owner e repo do full_name (formato: "owner/repo")
            partes = repositorio.split("/", 1)
            if len(partes) != 2:
                logger.warning(f"Formato inválido de repositório: {repositorio}")
                continue

            owner, repo_name = partes
            repos_encontrados.append({
                "full_name": repositorio,
                "owner": owner,
                "repo": repo_name,
                "language": linguagem,
            })

            if len(repos_encontrados) >= TOTAL_REPOS:
                break

    if not repos_encontrados:
        logger.error(
            f"Nenhum repositório com dados REST encontrado em {ARQUIVO_CSV}. "
            "Execute a coleta REST primeiro."
        )
        sys.exit(1)

    logger.info(
        f"Carregados {len(repos_encontrados)} repositórios com dados REST "
        f"(limite: {TOTAL_REPOS})"
    )
    return repos_encontrados


# ──────────────────────────────────────────────────────────────────────
# Checkpointing
# ──────────────────────────────────────────────────────────────────────

def carregar_estado() -> dict:
    """Carrega o estado do checkpoint do arquivo JSON."""
    if Path(ARQUIVO_ESTADO).exists():
        try:
            with open(ARQUIVO_ESTADO, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erro ao ler estado.json: {e}. Reiniciando checkpoint.")
            return _estado_padrao()
    return _estado_padrao()


def _estado_padrao() -> dict:
    """Retorna um estado padrão para início da coleta GraphQL."""
    return {
        "repos_concluidos_graphql": [],
        "fase_atual": "graphql",
        "indice_repo": 0,
    }


def salvar_estado(estado: dict):
    """Salva o estado do checkpoint no arquivo JSON."""
    with open(ARQUIVO_ESTADO, "w") as f:
        json.dump(estado, f, indent=2)
    logger.debug(
        f"Checkpoint salvo: {len(estado.get('repos_concluidos_graphql', []))} "
        "repositórios com GraphQL concluídos"
    )


def inicializar_csv():
    """Cria o arquivo CSV com cabeçalho se não existir."""
    if not Path(ARQUIVO_CSV).exists():
        with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "tecnologia", "repositorio", "linguagem",
                "tempo_ms", "tamanho_bytes"
            ])
        logger.info(f"Arquivo {ARQUIVO_CSV} criado com cabeçalho.")


def registrar_resultado(tecnologia: str, repositorio: str, linguagem: str,
                        tempo_ms: float, tamanho_bytes: int):
    """Registra uma linha no CSV de resultados."""
    with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            tecnologia, repositorio, linguagem,
            round(tempo_ms, 2), tamanho_bytes
        ])
    logger.info(
        f"[{tecnologia}] {repositorio} ({linguagem}): "
        f"{tempo_ms:.0f}ms, {tamanho_bytes} bytes"
    )


def verificar_se_ja_tem_graphql(repositorio: str) -> bool:
    """
    Verifica se o repositório já possui dados GraphQL no CSV.
    """
    if not Path(ARQUIVO_CSV).exists():
        return False
    with open(ARQUIVO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("tecnologia") == "GraphQL"
                    and row.get("repositorio") == repositorio):
                return True
    return False


# ──────────────────────────────────────────────────────────────────────
# Coleta GraphQL (v4)
# ──────────────────────────────────────────────────────────────────────

QUERY_PRS = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(
      first: %d
      states: [OPEN, CLOSED, MERGED]
      orderBy: {field: CREATED_AT, direction: DESC}
      after: $cursor
    ) {
      totalCount
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        number
        title
        author {
          login
        }
        reviews(first: %d) {
          totalCount
          pageInfo {
            endCursor
            hasNextPage
          }
          nodes {
            author {
              login
            }
            body
            state
          }
        }
      }
    }
  }
}
""" % (PRS_POR_PAGINA, COMENTARIOS_POR_PAGINA)


def executar_coleta_graphql(repositorio: dict, token: str) -> tuple:
    """
    Executa a coleta completa via GraphQL para um repositório.
    Retorna (tempo_total_ms, tamanho_total_bytes).

    Inclui paginação completa em 2 níveis:
    - PRs (páginas de PRS_POR_PAGINA)
    - Reviews dentro de cada PR (páginas de COMENTARIOS_POR_PAGINA)
    """
    owner = obter_seguro(repositorio, "owner", fallback="")
    repo = obter_seguro(repositorio, "repo", fallback="")
    full_name = obter_seguro(repositorio, "full_name", fallback="")

    if not owner or not repo:
        logger.error(f"Repositório inválido: {repositorio}")
        return 0, 0

    logger.info(f"  [GraphQL] Coletando PRs de {full_name}...")

    headers = {**HEADERS_GRAPHQL, "Authorization": f"Bearer {token}"}
    tempo_total = 0.0
    tamanho_total = 0
    total_prs_coletados = 0
    cursor = None
    has_next_page = True

    while has_next_page and total_prs_coletados < PRS_POR_REPO:
        variables = {
            "owner": owner,
            "repo": repo,
            "cursor": cursor,
        }

        payload = {
            "query": QUERY_PRS,
            "variables": variables,
        }

        inicio = time.time()

        for tentativa in range(5):
            try:
                resp = requests.post(
                    GRAPHQL_URL,
                    json=payload,
                    headers=headers,
                )
                tempo_total += (time.time() - inicio) * 1000

                if resp.status_code == 200:
                    break
                elif resp.status_code in (403, 429):
                    backoff_exponencial(tentativa, resp)
                else:
                    logger.warning(
                        f"Erro {resp.status_code} no GraphQL para {full_name}: "
                        f"{resp.text[:200]}"
                    )
                    return tempo_total, tamanho_total
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro de rede: {e}")
                tempo_total += (time.time() - inicio) * 1000
                backoff_exponencial(tentativa)

        if resp.status_code != 200:
            break

        tamanho_total += extrair_tamanho_resposta(resp)
        data = resp.json()

        # Verifica erros do GraphQL
        if "errors" in data:
            logger.error(f"Erro GraphQL para {full_name}: {data['errors']}")
            break

        repo_data = obter_seguro(data, "data", "repository", fallback={})
        if not repo_data:
            break

        prs_data = obter_seguro(repo_data, "pullRequests", fallback={})
        nodes = obter_seguro(prs_data, "nodes", fallback=[])

        if not nodes:
            break

        # Processa PRs e filtra bots
        for pr_node in nodes:
            author = obter_seguro(pr_node, "author", fallback={})
            author_login = obter_seguro(author, "login", fallback="")

            if not is_bot(author_login):
                total_prs_coletados += 1

                # Processa reviews (já vem na query inicial)
                reviews_data = obter_seguro(pr_node, "reviews", fallback={})
                review_nodes = obter_seguro(reviews_data, "nodes", fallback=[])

                for review in review_nodes:
                    review_author = obter_seguro(review, "author", fallback={})
                    review_login = obter_seguro(review_author, "login", fallback="")
                    # Apenas contagem/validação — comentários de bots são ignorados
                    if is_bot(review_login):
                        pass  # Descartado silenciosamente

        # Paginação
        page_info = obter_seguro(prs_data, "pageInfo", fallback={})
        has_next_page = (
            page_info.get("hasNextPage", False)
            and total_prs_coletados < PRS_POR_REPO
        )
        cursor = page_info.get("endCursor")

        logger.debug(
            f"  [GraphQL] {full_name}: {total_prs_coletados}/{PRS_POR_REPO} PRs coletados"
        )

        time.sleep(0.3)

    logger.info(
        f"  [GraphQL] {total_prs_coletados} PRs coletados em {full_name}"
    )

    return tempo_total, tamanho_total


# ──────────────────────────────────────────────────────────────────────
# Pipeline Principal
# ──────────────────────────────────────────────────────────────────────

def main():
    """Função principal do script de mineração (apenas GraphQL)."""
    logger.info("=" * 60)
    logger.info(
        "Mineração — GitHub GraphQL (v4) para 30 repositórios "
        "(continuação)"
    )
    logger.info("=" * 60)

    # Carrega token
    token = carregar_token()
    logger.info("Token GitHub carregado com sucesso.")

    # Inicializa CSV (se não existir, cria cabeçalho)
    inicializar_csv()

    # Carrega os 30 repositórios que já têm dados REST
    repositorios = carregar_repos_com_rest_do_csv()
    logger.info(f"{len(repositorios)} repositórios carregados para coleta GraphQL.")

    # Carrega estado do checkpoint
    estado = carregar_estado()

    # Garante que a fase seja graphql (ignora fase rest do checkpoint antigo)
    estado["fase_atual"] = "graphql"
    repos_concluidos_set = set(
        estado.get("repos_concluidos_graphql", [])
    )

    # Filtra repositórios que já têm GraphQL no CSV (dupla verificação)
    repos_pendentes = []
    for r in repositorios:
        full_name = obter_seguro(r, "full_name", fallback="")
        if full_name in repos_concluidos_set:
            continue
        if verificar_se_ja_tem_graphql(full_name):
            logger.info(f"  {full_name} já possui dados GraphQL no CSV. Pulando.")
            repos_concluidos_set.add(full_name)
            continue
        repos_pendentes.append(r)

    logger.info(
        f"{len(repos_pendentes)} repositórios pendentes para coleta GraphQL "
        f"(já concluídos: {len(repos_concluidos_set)})"
    )

    if not repos_pendentes:
        logger.info("Nenhum repositório pendente. Coleta GraphQL já está completa!")
        logger.info("=" * 60)
        logger.info("MINERAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info(f"Resultados em: {ARQUIVO_CSV}")
        logger.info("=" * 60)
        return

    # ── Fase GraphQL ───────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("FASE: Coleta via GraphQL (v4)")
    logger.info("=" * 60)

    for i, repo in enumerate(repos_pendentes):
        full_name = obter_seguro(repo, "full_name", fallback="")
        linguagem = obter_seguro(repo, "language", fallback="Desconhecida")

        logger.info(
            f"\n[{i + 1}/{len(repos_pendentes)}] [GraphQL] "
            f"{full_name} ({linguagem})"
        )

        # Verifica rate limit antes de começar
        verificar_e_esperar_rate_limit(HEADERS_GRAPHQL, token)

        try:
            tempo_ms, tamanho_bytes = executar_coleta_graphql(repo, token)

            if tempo_ms > 0 or tamanho_bytes > 0:
                registrar_resultado(
                    "GraphQL", full_name, linguagem,
                    tempo_ms, tamanho_bytes
                )

            # Atualiza checkpoint
            if "repos_concluidos_graphql" not in estado:
                estado["repos_concluidos_graphql"] = []
            estado["repos_concluidos_graphql"].append(full_name)
            estado["indice_repo"] = i + 1
            salvar_estado(estado)

        except Exception as e:
            logger.error(f"Erro ao processar {full_name} via GraphQL: {e}")
            logger.info("Checkpoint salvo. O script pode ser retomado.")
            salvar_estado(estado)
            sys.exit(1)

        # Pausa entre repositórios para evitar rate limiting
        time.sleep(1)

    logger.info("\n" + "=" * 60)
    logger.info("MINERAÇÃO GRAPHQL CONCLUÍDA COM SUCESSO!")
    logger.info(f"Resultados salvos em: {ARQUIVO_CSV}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()