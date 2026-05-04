# Trabalho 2 — Engenharia de dados (Spark, Delta Lake, MinIO, SQL Server)

**Documentação publicada (GitHub Pages):** [https://octaviodemos.github.io/trabalho2ed-minio-sql/](https://octaviodemos.github.io/trabalho2ed-minio-sql/)

> A URL acima corresponde ao site gerado por `mkdocs gh-deploy` (por exemplo `uv run task docs_deploy`). Se o GitHub Pages ainda não estiver configurado ou o deploy não tiver sido executado, o link pode responder **404** até a publicação estar concluída.

Projeto complementar ao Trabalho 1: infraestrutura em Docker (SQL Server 2025 + MinIO), extração via PySpark para a camada **landing-zone** (CSV no bucket MinIO), preparando a arquitetura medalhão (landing → bronze Delta).

## Pré-requisitos

- Docker e Docker Compose
- [UV](https://docs.astral.sh/uv/) (Python 3.11)
- **Dependências de sistema (Linux/Ubuntu)**:
  ```bash
  sudo apt-get update && sudo apt-get install -y unixodbc unixodbc-dev

  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
  curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
  sudo apt-get update && sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
  ```
  (Necessário para conexões ODBC via `pyodbc` nos notebooks Jupyter.)

## 1. Variáveis de ambiente

```bash
cp .env.example .env
```

Editar `.env`: senha forte do SA (`MSSQL_SA_PASSWORD`), credenciais do MinIO e, se necessário, `MSSQL_JDBC_URL` ou `MINIO_S3_ENDPOINT` (por exemplo `http://127.0.0.1:9000` quando o notebook corre no anfitrião com a API MinIO exposta na porta `9000`).

## 2. Subir a infraestrutura

```bash
docker compose up -d
```

| Serviço       | Descrição               | Portas no anfitrião |
|---------------|-------------------------|----------------------|
| SQL Server    | Developer Edition 2025  | `1433`               |
| MinIO API     | API compatível com S3   | `9000`               |
| MinIO Console | Interface web           | `9001`               |

O serviço `minio-init` cria o bucket `landing-zone` se ainda não existir.

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

O ficheiro `run_mkdocs.py` contorna uma limitação do **MkDocs 1.6** ao resolver o diretório do tema **Material** sem carregar o pacote `material` prematuramente. Se `uv run task docs_build` falhar com `No module named 'material.plugins'`, a instalação do `mkdocs-material` no `.venv` pode estar incompleta (ocorre por vezes em caminhos `/mnt/c` no WSL): apague a pasta `.venv` a partir do Explorador de ficheiros do Windows ou mova o projeto para um disco Linux nativo (`$HOME/...`) e execute `uv sync` de novo.

## Stack principal

- SQL Server 2025 (Docker)
- MinIO (Docker)
- Apache Spark 3.5.3 (PySpark)
- Delta Lake 3.2.0
- Python 3.11 + UV

---

## Segurança

O ficheiro `.env` com credenciais reais **não** deve ser versionado; mantém-se apenas `.env.example` como modelo.

---

## 📚 Referências

- **Canal DataWay BR (YouTube):** [https://www.youtube.com/@DataWayBR](https://www.youtube.com/@DataWayBR) (conteúdo sobre Spark, *data lakes* e engenharia de dados).
- **Repositório de exemplo (professor Jorge Luiz da Silva):** [github.com/jlsilva01/spark-delta-minio-sqlserver](https://github.com/jlsilva01/spark-delta-minio-sqlserver)
- **Material de apoio SATC:** *Python para Engenharia de Dados* (PDF e materiais disponibilizados na disciplina).
