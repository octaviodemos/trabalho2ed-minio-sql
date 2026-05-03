# Trabalho 2 — Engenharia de dados (Spark, Delta Lake, MinIO, SQL Server)

Projeto complementar ao Trabalho 1: infraestrutura em Docker (SQL Server 2025 + MinIO), extração via PySpark para a camada **landing-zone** (CSV no bucket MinIO), preparando a arquitetura medalhão (landing → bronze Delta).

## Pré-requisitos

- Docker e Docker Compose
- [UV](https://docs.astral.sh/uv/) (Python 3.11)
- **Dependências de sistema (Linux/Ubuntu)**:
  ```bash
  # Instalar bibliotecas ODBC
  sudo apt-get update && sudo apt-get install -y unixodbc unixodbc-dev
  
  # Instalar driver ODBC do SQL Server
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
  curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
  sudo apt-get update && sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
  ```
  (Necessário para suportar conexões ODBC via `pyodbc` aos notebooks Jupyter)

## 1. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env`: senha forte do SA (`MSSQL_SA_PASSWORD`), usuário/senha do MinIO e, se necessário, `MSSQL_JDBC_DATABASE`, `MSSQL_JDBC_URL` ou `MINIO_S3_ENDPOINT` (use `http://127.0.0.1:9000` quando o notebook roda no host e o MinIO está no Compose com porta `9000` publicada).

## 2. Subir a infraestrutura

```bash
docker compose up -d
```

Serviços:

| Serviço    | Descrição              | Portas host      |
|-----------|-------------------------|------------------|
| SQL Server | Developer Edition 2025 | `1433`           |
| MinIO API  | API compatível com S3  | `9000`           |
| MinIO Console | Interface web       | `9001`           |

O serviço `minio-init` cria o bucket `landing-zone` se ainda não existir.

## 3. Ambiente Python (UV)

Instale as dependências Python:

```bash
uv sync
```

**Importante**: Antes de executar os notebooks, certifique-se de que as dependências ODBC de sistema estão instaladas (veja "Pré-requisitos" acima). Sem isso, o `pyodbc` não conseguirá se conectar ao SQL Server.

Executar o JupyterLab na pasta `notebook/`:

```bash
uv run jupyter lab notebook/
```

Rode as células do 00_setup_sqlserver.ipynb em ordem. Cada execução da parte de carga apaga e recria os dados a partir dos CSV
Abra `notebook/01_extracao_sqlserver_landing_zone.ipynb`, configure o `.env` e execute as células.

## Referências de modelo

- [spark-delta-minio-sqlserver](https://github.com/jlsilva01/spark-delta-minio-sqlserver) (repositório de referência do professor Jorge Luiz da Silva)
- [spark-delta](https://github.com/jlsilva01/spark-delta)

## Stack principal

- SQL Server 2025 (Docker)
- MinIO (Docker)
- Apache Spark 3.5.3 (PySpark)
- Delta Lake 3.2.0
- Python 3.11 + UV
