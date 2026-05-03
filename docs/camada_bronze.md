# Camada Bronze

## Objetivo

A camada Bronze é a **primeira camada tipada** da Arquitetura Medalhão. Ela recebe os dados crus da Landing Zone (CSV) e os transforma em formato **Delta Lake** com:

- **Schema enforcement**: tipagem forte aplicada na leitura
- **Metadados de auditoria**: rastreabilidade da carga
- **Formato transacional**: suporte a ACID, versionamento e time travel

## Pipeline

```
s3a://landing-zone/dbo_Categoria/*.csv
        │
        ▼
  Spark read (CSV + schema)
        │
        ▼
  Adiciona colunas de auditoria:
    • _bronze_loaded_at
    • _bronze_source_file
        │
        ▼
  Spark write (Delta Lake)
        │
        ▼
s3a://bronze/dbo_Categoria/
    ├── _delta_log/
    │   └── 00000000000000000000.json
    └── part-00000-*.snappy.parquet
```

## Tabelas processadas

| Tabela | Schema | Linhas esperadas |
|---|---|---|
| `dbo_Categoria` | id_categoria, nome, descricao | 5 |
| `dbo_Autor` | id_autor, nome, nacionalidade, data_nascimento | 10 |
| `dbo_Livro` | id_livro, titulo, isbn, ano_publicacao, id_categoria, id_autor | 20 |
| `dbo_Membro` | id_membro, nome, email, telefone, data_cadastro | 15 |
| `dbo_Emprestimo` | id_emprestimo, id_livro, id_membro, datas, status | 30 |
| `dbo_Multa` | id_multa, id_emprestimo, valor, pago, data_geracao | 8 |

## Colunas de auditoria

Cada registro na camada Bronze recebe duas colunas adicionais:

| Coluna | Tipo | Descrição |
|---|---|---|
| `_bronze_loaded_at` | String (ISO 8601) | Timestamp de quando o registro foi ingerido na Bronze |
| `_bronze_source_file` | String | Caminho S3 do arquivo CSV de origem |

## Como executar

```bash
# Certifique-se de que os containers estão no ar
docker compose up -d

# Abra o JupyterLab
uv run jupyter lab notebook/

# Execute o notebook 02
# notebook/02_landing_to_bronze_delta.ipynb
```

!!! warning "Pré-requisito"
    Os notebooks `00_setup_sqlserver.ipynb` e `01_extracao_sqlserver_landing_zone.ipynb` devem ter sido executados com sucesso antes deste.
