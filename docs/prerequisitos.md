# Pré-requisitos de sistema e configuração

Esta página condensa o que está no **README** do repositório: Docker, UV, ODBC para `pyodbc`, variáveis `.env`, buckets MinIO e dependência **boto3** nos notebooks.

## Docker e UV

- **Docker** e **Docker Compose** para SQL Server e MinIO (`docker compose up -d`).
- **[UV](https://docs.astral.sh/uv/)** com Python 3.11 (`uv sync`, `uv run jupyter lab notebook/`).

## ODBC (notebook `00_setup_sqlserver.ipynb`)

Instale primeiro **unixODBC**:

```bash
sudo apt-get update && sudo apt-get install -y unixodbc unixodbc-dev
```

Depois **um** dos drivers para SQL Server:

**Microsoft ODBC Driver 18** (ajuste `ubuntu/24.04` à sua LTS):

```bash
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update && sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**FreeTDS** (alternativa simples no Ubuntu):

```bash
sudo apt-get install -y tdsodbc
```

O notebook **escolhe automaticamente** o primeiro driver disponível entre *ODBC Driver 18/17/13 for SQL Server* e *FreeTDS*. Para forçar um nome, defina no `.env`:

```text
MSSQL_ODBC_DRIVER={ODBC Driver 18 for SQL Server}
```

## Ficheiro `.env`

```bash
cp .env.example .env
```

Edite credenciais reais. **Se a senha contiver `#`, use aspas** em volta do valor — em ficheiros `.env`, `#` inicia comentário e pode truncar senhas (afetando `MSSQL_SA_PASSWORD` no Docker e ligações JDBC/ODBC).

## Buckets MinIO (`landing-zone`, `bronze`)

O **`docker-compose`** inclui o serviço **`minio-init`**, que cria os dois buckets se não existirem.

Os notebooks **`01_extracao_sqlserver_landing_zone.ipynb`** e **`02_landing_to_bronze_delta.ipynb`** repetem essa garantia com a API S3 (**boto3**), de forma idempotente, quando o init não foi executado ou falhou.

## Python

A dependência **boto3** está declarada no `pyproject.toml` e é instalada com `uv sync`.

## MkDocs (erro `material.plugins`)

O tema **Material** para MkDocs expõe plugins em `material.plugins.*`. Se o `uv sync` gravou um pacote **incompleto** (por exemplo em disco **Windows montado em `/mnt/c`** no WSL), a pasta `plugins` pode faltar dentro de `site-packages/material/` e o comando `uv run task docs_build` falha com esse import.

**Corrigir** (na raiz do projeto, com o `.venv` ativo):

```bash
uv pip install --force-reinstall "mkdocs-material>=9.7.6"
```

Confirme que existe `material/plugins` no site-packages:

```bash
ls .venv/lib/python3.11/site-packages/material/plugins
```

Se o problema persistir, apague a pasta `.venv`, execute `uv sync` de novo ou trabalhe num clone do repositório em disco **Linux nativo** (por exemplo `~/projetos/...`), onde instalações pip tendem a ser mais estáveis do que em sistemas de ficheiros montados do Windows.
