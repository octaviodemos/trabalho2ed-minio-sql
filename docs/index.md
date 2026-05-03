# Trabalho 2 — Engenharia de Dados

Projeto complementar ao Trabalho 1: infraestrutura em Docker (SQL Server 2025 + MinIO), extração via PySpark para a camada **landing-zone** (CSV no bucket MinIO), e transformação para a camada **Bronze** em formato **Delta Lake**.

## Stack principal

| Tecnologia | Versão | Papel |
|---|---|---|
| SQL Server | 2025 (Docker) | Banco de dados relacional (origem) |
| MinIO | RELEASE.2025-02 | Object Storage compatível com S3 |
| Apache Spark | 3.5.3 (PySpark) | Engine de processamento distribuído |
| Delta Lake | 3.2.0 | Formato de armazenamento ACID |
| Python | 3.11 + UV | Gerenciamento de ambiente |

## Notebooks

| # | Notebook | Descrição |
|---|---|---|
| 00 | `00_setup_sqlserver.ipynb` | Cria o banco `BibliotecaDb` e popula tabelas a partir dos CSV |
| 01 | `01_extracao_sqlserver_landing_zone.ipynb` | Extrai tabelas do SQL Server → CSV no bucket `landing-zone` |
| 02 | `02_landing_to_bronze_delta.ipynb` | Lê CSV da landing-zone e grava em Delta Lake no bucket `bronze` |

## Como executar

```bash
# 1. Subir a infraestrutura
docker compose up -d

# 2. Instalar dependências Python
uv sync

# 3. Abrir JupyterLab
uv run jupyter lab notebook/
```

Rode os notebooks na ordem: `00` → `01` → `02`.
