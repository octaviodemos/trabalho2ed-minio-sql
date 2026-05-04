# Camada Bronze

## Objetivo

A camada Bronze corresponde à **primeira materialização tipada** da arquitetura medalhão. Os ficheiros CSV provenientes da *landing zone* são lidos pelo Spark com *schema enforcement*, enriquecidos com metadados de linhagem temporal e de ficheiro de origem, e persistidos em **Delta Lake** no MinIO, o que habilita transações ACID, versionamento e consultas de *time travel* sobre o histórico de versões.

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

---

## DML na Bronze — exemplos do `dml_bronze.ipynb`

Após a carga Delta no MinIO, o notebook `dml_bronze.ipynb` demonstra mutações sobre o caminho `s3a://bronze/dbo_Categoria/` e a leitura do registo transacional do Delta. Os excertos abaixo reproduzem a lógica principal; o caminho e a variável `novo_id` devem estar coerentes com a execução sequencial das células do notebook.

### INSERT (registo sintético de validação)

```python
import pyspark.sql.functions as F

BRONZE_TABLE_PATH = "s3a://bronze/dbo_Categoria/"
df_atual = spark.read.format("delta").load(BRONZE_TABLE_PATH)
proximo_id = df_atual.select(F.max(F.col("id_categoria")).alias("m")).first()["m"]
base_id = int(proximo_id) if proximo_id is not None else 0
novo_id = base_id + 1

linha_nova = spark.range(1).select(
    F.lit(novo_id).cast("int").alias("id_categoria"),
    F.lit("Categoria fictícia (INSERT DML)").alias("nome"),
    F.lit("Registro sintético para validar escrita ACID na Bronze.").alias("descricao"),
    F.date_format(
        F.current_timestamp(), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
    ).alias("_bronze_loaded_at"),
    F.lit("dml_bronze.ipynb#INSERT").alias("_bronze_source_file"),
)

linha_nova.write.format("delta").mode("append").save(BRONZE_TABLE_PATH)
```

### UPDATE (correção pontual, `id_categoria = 1`)

```python
import pyspark.sql.functions as F
from delta.tables import DeltaTable

BRONZE_TABLE_PATH = "s3a://bronze/dbo_Categoria/"
tabela_delta = DeltaTable.forPath(spark, BRONZE_TABLE_PATH)

tabela_delta.update(
    condition="id_categoria = 1",
    set={
        "descricao": F.lit(
            "Descrição revisada na Bronze (UPDATE via DeltaTable)."
        )
    },
)

spark.read.format("delta").load(BRONZE_TABLE_PATH).filter(
    F.col("id_categoria") == F.lit(1)
).select("id_categoria", "nome", "descricao").show(truncate=False)
```

### DELETE (expurgo do identificador sintético)

```python
import pyspark.sql.functions as F
from delta.tables import DeltaTable

BRONZE_TABLE_PATH = "s3a://bronze/dbo_Categoria/"
tabela_delta = DeltaTable.forPath(spark, BRONZE_TABLE_PATH)
tabela_delta.delete(F.col("id_categoria") == F.lit(novo_id))
```

A variável `novo_id` corresponde ao identificador criado no bloco **INSERT** do mesmo fluxo de execução.

### Auditoria — `history()`

```python
import pyspark.sql.functions as F
from delta.tables import DeltaTable

tabela_delta = DeltaTable.forPath(spark, "s3a://bronze/dbo_Categoria/")
tabela_delta.history().select(
    "version",
    "timestamp",
    "operation",
    "operationParameters",
).orderBy(F.col("version").desc()).show(20, truncate=80)
```

Para a distinção entre tabelas **geridas** e **externas** no Spark, e para o efeito de `DROP TABLE` sobre dados em `s3a://`, consultar a página [Tabelas gerenciadas vs não gerenciadas](tabelas_gerenciadas_vs_nao_gerenciadas.md).
