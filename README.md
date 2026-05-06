# Trabalho 2 — Engenharia de dados (Spark, Delta Lake, MinIO, SQL Server)

**Documentação publicada (GitHub Pages):** [https://octaviodemos.github.io/trabalho2ed-minio-sql/](https://octaviodemos.github.io/trabalho2ed-minio-sql/)

> A URL acima corresponde ao site gerado por `mkdocs gh-deploy` (por exemplo `uv run task docs_deploy`). Se o GitHub Pages ainda não estiver configurado ou o deploy não tiver sido executado, o link pode responder **404** até a publicação estar concluída.

Projeto complementar ao Trabalho 1: infraestrutura em Docker (SQL Server 2025 + MinIO), extração via PySpark para a camada **landing-zone** (CSV no bucket MinIO), preparando a arquitetura medalhão (landing → bronze Delta).

## Pré-requisitos

- Docker e Docker Compose
- [UV](https://docs.astral.sh/uv/) (Python 3.11)
- **Dependências de sistema (Linux/Ubuntu)** para `pyodbc` no notebook `00`:
  - **Base** (obrigatória): `unixodbc` e `unixodbc-dev`.
  - **Driver SQL Server** — instale **uma** das opções abaixo. O notebook `00` escolhe automaticamente o primeiro driver disponível entre *ODBC Driver 18/17/13 for SQL Server* e *FreeTDS*; para forçar um nome concreto, defina `MSSQL_ODBC_DRIVER` no `.env` (ver `.env.example`).

  **Opção A — Microsoft ODBC Driver 18** (ajuste `ubuntu/24.04` se usar outra LTS):

  ```bash
  sudo apt-get update && sudo apt-get install -y unixodbc unixodbc-dev

  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
  curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
  sudo apt-get update && sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
  ```

  **Opção B — FreeTDS** (pacote `tdsodbc`):

  ```bash
  sudo apt-get update && sudo apt-get install -y unixodbc unixodbc-dev tdsodbc
  ```

## 1. Variáveis de ambiente

Copiar o modelo e editar valores reais:

```bash
cp .env.example .env
```

Incluir senha forte do SA (`MSSQL_SA_PASSWORD`), credenciais do MinIO e, se necessário, `MSSQL_JDBC_URL` ou `MINIO_S3_ENDPOINT` (por exemplo `http://127.0.0.1:9000` quando o notebook corre no anfitrião com a API MinIO exposta na porta `9000`). **Se a senha contiver o carácter `#`, coloque o valor entre aspas** — em ficheiros `.env`, `#` inicia comentário e trunca o valor (afetando também `MSSQL_SA_PASSWORD` passado ao Docker).

## 2. Subir a infraestrutura

```bash
docker compose up -d
```

| Serviço       | Descrição               | Portas no anfitrião |
|---------------|-------------------------|----------------------|
| SQL Server    | Developer Edition 2025  | `1433`               |
| MinIO API     | API compatível com S3   | `9000`               |
| MinIO Console | Interface web           | `9001`               |

O serviço `minio-init` cria os buckets `landing-zone` e `bronze` se ainda não existirem. Os notebooks `01` e `02` complementam isso com criação idempotente via API S3 (**boto3**), útil quando o MinIO sobe sem o `minio-init` ou o serviço falha.

## 3. Ambiente Python (UV)

```bash
uv sync
```

Antes dos notebooks, confirmar que as dependências ODBC de sistema estão instaladas (secção «Pré-requisitos»).

```bash
uv run jupyter lab notebook/
```

Executar os notebooks na ordem: `00_setup_sqlserver.ipynb` → `01_extracao_sqlserver_landing_zone.ipynb` → `02_landing_to_bronze_delta.ipynb`; opcionalmente `dml_bronze.ipynb` após a Bronze estar materializada.

## Documentação local (MkDocs)

```bash
uv run task docs_serve
```

Publicação no GitHub Pages:

```bash
uv run task docs_deploy
```

O ficheiro `run_mkdocs.py` contorna uma limitação do **MkDocs 1.6** ao resolver o diretório do tema **Material** sem carregar o pacote `material` prematuramente.

Se `uv run task docs_build` falhar com **`No module named 'material.plugins'`**, o pacote **mkdocs-material** no `.venv` ficou **incompleto** (falta a pasta `material/plugins` — comum em projetos sobre **`/mnt/c`** no WSL). Tente primeiro:

```bash
uv pip install --force-reinstall "mkdocs-material>=9.7.6"
```

Se continuar a falhar: apague `.venv`, volte a correr `uv sync`, ou clone o repositório para um caminho **Linux nativo** (`$HOME/...`). Detalhes na secção **MkDocs** em `docs/prerequisitos.md` (também no site gerado pelo MkDocs).

## Stack principal

- SQL Server 2025 (Docker)
- MinIO (Docker)
- Apache Spark 3.5.3 (PySpark)
- Delta Lake 3.2.0
- Python 3.11 + UV
- **boto3** (criação de buckets MinIO a partir dos notebooks, alinhada ao `minio-init`)

---

## Segurança

O ficheiro `.env` com credenciais reais **não** deve ser versionado; mantém-se apenas `.env.example` como modelo.

---

## 📚 Referências

- **Canal DataWay BR (YouTube):** [https://www.youtube.com/@DataWayBR](https://www.youtube.com/@DataWayBR) (conteúdo sobre Spark, *data lakes* e engenharia de dados).
- **Repositório de exemplo (professor Jorge Luiz da Silva):** [github.com/jlsilva01/spark-delta-minio-sqlserver](https://github.com/jlsilva01/spark-delta-minio-sqlserver)
- **Material de apoio SATC:** *Python para Engenharia de Dados* (PDF e materiais disponibilizados na disciplina).
