# Tabelas Gerenciadas vs Não Gerenciadas no Delta Lake

## Introdução

No ecossistema Spark + Delta Lake, existem dois tipos fundamentais de tabelas: **Gerenciadas** (Managed) e **Não Gerenciadas** (Unmanaged / External). A diferença entre elas impacta diretamente o **ciclo de vida dos dados**, a **portabilidade** e a **governança** do seu Data Lakehouse.

!!! info "Contexto do projeto"
    No nosso projeto **BibliotecaDb**, utilizamos **tabelas não gerenciadas** na camada Bronze, pois os dados ficam armazenados no MinIO (Object Storage S3) e precisamos de controle total sobre o ciclo de vida dos arquivos.

No MinIO, as tabelas Delta são **externas ao catálogo padrão do Spark**: o armazenamento efetivo situa-se sob um prefixo `s3a://bronze/...` definido pelo projeto, sendo o motor responsável apenas por referenciar esse local. Tal configuração favorece a **persistência dos dados**, na medida em que os objetos (Parquet, `_delta_log`, *manifests*) permanecem no *bucket* após recriação de `SparkSession`, alteração de *cluster* ou remoção da entrada no catálogo, bastando reutilizar o mesmo URI para releitura ou *time travel*. Num cenário **gerido** no *warehouse* local, acumulam-se riscos de misturar dados efémeros de laboratório com o disco do *cluster* e de perda associada a `DROP TABLE` ou a desmantelamento de infraestrutura. No modelo **externo no MinIO**, o *object store* constitui a fonte de verdade durável: políticas de retenção, cópias de segurança e replicação aplicam-se diretamente aos ficheiros Delta, em linha com desenhos de *data lakehouse* em produção.

---

## Comparativo Geral

| Aspecto | Tabela Gerenciada | Tabela Não Gerenciada |
|---|---|---|
| **Quem controla os dados?** | O Spark/Metastore | O usuário/engenheiro |
| **Localização dos dados** | Diretório padrão do warehouse (`spark-warehouse/`) | Caminho definido pelo usuário (S3, HDFS, local) |
| **O que acontece no `DROP TABLE`?** | **Metadados E dados são apagados** | **Apenas metadados são apagados**; dados permanecem |
| **Portabilidade** | Baixa (preso ao metastore) | Alta (dados independentes do catálogo) |
| **Caso de uso ideal** | Tabelas temporárias, sandbox, experimentos | Data Lakes, produção, dados compartilhados |

---

## Tabela Gerenciada (Managed Table)

Uma tabela gerenciada é **totalmente controlada pelo catálogo do Spark**. Quando você cria uma tabela gerenciada, o Spark decide onde armazenar os arquivos (normalmente no diretório `spark-warehouse/`). Quando a tabela é removida com `DROP TABLE`, **os dados são deletados permanentemente junto com os metadados**.

### Criação — Exemplo com dados do BibliotecaDb

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

spark = SparkSession.builder \
    .appName("exemplo-tabela-gerenciada") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Schema da tabela Categoria
schema_categoria = StructType([
    StructField("id_categoria", IntegerType(), False),
    StructField("nome", StringType(), False),
    StructField("descricao", StringType(), True),
])

# Dados de exemplo
dados = [
    (1, "Romance", "Ficção narrativa centrada em relacionamentos"),
    (2, "Ficção Científica", "Narrativas com tecnologia futura"),
    (3, "Técnico", "Obras sobre informática e engenharia"),
    (4, "História", "Livros sobre o passado e sociedades"),
    (5, "Infantil", "Literatura para o público infantil"),
]

df = spark.createDataFrame(dados, schema_categoria)
```

=== "SQL"

    ```sql
    -- Criação de tabela gerenciada via SQL
    -- Os dados serão armazenados em spark-warehouse/categoria_managed/
    CREATE TABLE categoria_managed
    USING DELTA
    AS SELECT * FROM temp_categoria;
    ```

=== "PySpark (DataFrame API)"

    ```python
    # Criação de tabela gerenciada via DataFrame API
    # saveAsTable() SEM path = tabela GERENCIADA
    df.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable("categoria_managed")
    ```

### Verificando o tipo da tabela

```python
# Exibe informações detalhadas sobre a tabela
spark.sql("DESCRIBE EXTENDED categoria_managed").show(truncate=False)
```

A saída incluirá:

```
+----------------------------+--------------------------------------------------+
| info_name                  | info_value                                       |
+----------------------------+--------------------------------------------------+
| Type                       | MANAGED                                          |
| Location                   | file:/path/to/spark-warehouse/categoria_managed  |
+----------------------------+--------------------------------------------------+
```

!!! warning "Cuidado com DROP TABLE"
    ```sql
    -- PERIGO: isso apaga os DADOS e os METADADOS!
    DROP TABLE categoria_managed;
    ```
    Após esse comando, os arquivos Parquet/Delta em `spark-warehouse/categoria_managed/` são **permanentemente removidos**. Não há como recuperá-los sem backup.

---

## Tabela Não Gerenciada (External / Unmanaged Table)

Uma tabela não gerenciada armazena os dados em um **caminho definido pelo usuário**. O catálogo do Spark mantém apenas uma referência (ponteiro) para esse caminho. Quando a tabela é removida com `DROP TABLE`, **apenas os metadados do catálogo são apagados** — os dados permanecem intactos no caminho original.

### Persistência em `s3a://` e semântica do `DROP TABLE`

Quando a `LOCATION` ou o `save()` apontam para um prefixo **S3A** no MinIO (por exemplo `s3a://bronze/dbo_Categoria/`), os ficheiros de dados Parquet, o diretório `_delta_log` e demais artefactos do Delta **residem no armazenamento objeto** (*object store*), não no disco local do processo Spark. Por conseguinte, um `DROP TABLE` executado no catálogo Spark **remove a entrada de catálogo** (e eventualmente metadados do *metastore*, conforme a configuração), mas **não invoca, por si só, a eliminação recursiva dos objetos no *bucket***: o conteúdo físico permanece acessível mediante nova `CREATE TABLE ... LOCATION` ou `DeltaTable.forPath` sobre o mesmo URI. Esta propriedade é central para a **governança e recuperação** em *data lakes*: desacopla o ciclo de vida do motor analítico do armazenamento duradouro, permitindo políticas de retenção, *backup* e auditoria ao nível do MinIO/S3.

### Criação — Exemplo com dados no MinIO (nosso projeto)

Essa é a abordagem utilizada na nossa **camada Bronze**:

=== "PySpark (DataFrame API) — Como usamos no projeto"

    ```python
    # Caminho no MinIO (Object Storage)
    bronze_path = "s3a://bronze/dbo_Categoria/"

    # save() COM path explícito = tabela NÃO GERENCIADA
    df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(bronze_path)

    # Registrar como tabela SQL (opcional — cria referência no catálogo)
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS categoria_bronze
        USING DELTA
        LOCATION '{bronze_path}'
    """)
    ```

=== "SQL"

    ```sql
    -- A palavra-chave LOCATION torna a tabela NÃO GERENCIADA
    CREATE TABLE categoria_bronze
    USING DELTA
    LOCATION 's3a://bronze/dbo_Categoria/';
    ```

=== "DeltaTable API (leitura direta)"

    ```python
    from delta.tables import DeltaTable

    # Leitura direta pelo caminho — sem precisar de catálogo
    dt = DeltaTable.forPath(spark, "s3a://bronze/dbo_Categoria/")
    dt.toDF().show()

    # Consultar histórico de versões
    dt.history().show()
    ```

### Verificando o tipo da tabela

```python
spark.sql("DESCRIBE EXTENDED categoria_bronze").show(truncate=False)
```

A saída incluirá:

```
+----------------------------+----------------------------------------------+
| info_name                  | info_value                                   |
+----------------------------+----------------------------------------------+
| Type                       | EXTERNAL                                     |
| Location                   | s3a://bronze/dbo_Categoria                   |
+----------------------------+----------------------------------------------+
```

!!! tip "Segurança ao dropar"
    ```sql
    -- SEGURO: isso apaga apenas a referência do catálogo
    DROP TABLE categoria_bronze;
    ```
    Os arquivos Delta em `s3a://bronze/dbo_Categoria/` **continuam existindo** no MinIO. Você pode recriá-la a qualquer momento com um novo `CREATE TABLE ... LOCATION`.

---

## Demonstração prática: Operações CRUD no Delta Lake

### INSERT — Adicionando dados

=== "Tabela Gerenciada"

    ```python
    # Inserir novos registros via append
    novos_dados = [(6, "Poesia", "Obras em verso")]
    df_novos = spark.createDataFrame(novos_dados, schema_categoria)

    df_novos.write \
        .format("delta") \
        .mode("append") \
        .saveAsTable("categoria_managed")  # saveAsTable → gerenciada
    ```

=== "Tabela Não Gerenciada"

    ```python
    # Inserir novos registros via append no caminho externo
    novos_dados = [(6, "Poesia", "Obras em verso")]
    df_novos = spark.createDataFrame(novos_dados, schema_categoria)

    df_novos.write \
        .format("delta") \
        .mode("append") \
        .save("s3a://bronze/dbo_Categoria/")  # save(path) → não gerenciada
    ```

### UPDATE — Atualizando registros

```python
from delta.tables import DeltaTable
from pyspark.sql.functions import lit

# Funciona igualmente para ambos os tipos de tabela
# A diferença é apenas como você referencia (nome vs caminho)

# ── Via nome (gerenciada registrada no catálogo) ──
dt = DeltaTable.forName(spark, "categoria_managed")

# ── Via caminho (não gerenciada) ──
dt = DeltaTable.forPath(spark, "s3a://bronze/dbo_Categoria/")

# Operação de UPDATE (igual para ambas)
dt.update(
    condition="id_categoria = 3",
    set={"descricao": lit("Obras sobre informática, ciência de dados e engenharia de software")}
)
```

### DELETE — Removendo registros

```python
from delta.tables import DeltaTable

# Via caminho (não gerenciada — nosso caso no projeto)
dt = DeltaTable.forPath(spark, "s3a://bronze/dbo_Categoria/")

# Deletar a categoria "Poesia"
dt.delete("id_categoria = 6")

# Verificar resultado
dt.toDF().orderBy("id_categoria").show()
```

### MERGE (Upsert) — Inserir ou atualizar

O `MERGE` é uma das operações mais poderosas do Delta Lake. Ele permite fazer **upsert** (insert + update) em uma única operação atômica:

```python
from delta.tables import DeltaTable

# Tabela alvo (Bronze no MinIO)
dt = DeltaTable.forPath(spark, "s3a://bronze/dbo_Categoria/")

# Novos dados (podem conter registros novos e atualizações)
dados_atualizados = [
    (3, "Técnico", "Obras sobre TI, ciência de dados e métodos aplicados"),  # UPDATE
    (6, "Poesia", "Coletâneas de poemas e literatura em verso"),              # INSERT
]
df_updates = spark.createDataFrame(dados_atualizados, schema_categoria)

# MERGE: atualiza se existir, insere se não existir
(
    dt.alias("alvo")
    .merge(
        df_updates.alias("origem"),
        "alvo.id_categoria = origem.id_categoria"
    )
    .whenMatchedUpdateAll()       # Se encontrar: atualiza todos os campos
    .whenNotMatchedInsertAll()    # Se não encontrar: insere novo registro
    .execute()
)

# Verificar resultado
dt.toDF().orderBy("id_categoria").show(truncate=False)
```

---

## Time Travel (Viagem no Tempo)

O Delta Lake mantém um **log transacional** que permite consultar versões anteriores dos dados:

```python
from delta.tables import DeltaTable

# ── Consultar uma versão específica ──
df_v0 = (
    spark.read
    .format("delta")
    .option("versionAsOf", 0)           # Versão 0 (estado inicial)
    .load("s3a://bronze/dbo_Categoria/")
)
df_v0.show()

# ── Consultar por timestamp ──
df_ontem = (
    spark.read
    .format("delta")
    .option("timestampAsOf", "2026-05-01")
    .load("s3a://bronze/dbo_Categoria/")
)
df_ontem.show()

# ── Ver todo o histórico de operações ──
dt = DeltaTable.forPath(spark, "s3a://bronze/dbo_Categoria/")
dt.history().select("version", "timestamp", "operation", "operationMetrics").show(truncate=False)
```

---

## Quando usar cada tipo?

### Use Tabela Gerenciada quando:

- ✅ Você está **experimentando** ou fazendo análises exploratórias
- ✅ Os dados são **temporários** e podem ser recriados facilmente
- ✅ Você quer que o Spark gerencie o ciclo de vida completo
- ✅ Ambiente de **sandbox** ou desenvolvimento local

### Use Tabela Não Gerenciada quando:

- ✅ Os dados residem em **Object Storage** (MinIO, S3, GCS, ADLS)
- ✅ Múltiplas ferramentas ou equipes acessam os mesmos dados
- ✅ Você precisa de **controle sobre o ciclo de vida** dos arquivos
- ✅ Ambiente de **produção** ou Data Lakehouse
- ✅ Implementação de **Arquitetura Medalhão** (nosso caso!)

!!! success "Decisão do projeto"
    No nosso projeto **BibliotecaDb**, escolhemos **tabelas não gerenciadas** para a camada Bronze porque:

    1. Os dados ficam no **MinIO** (Object Storage externo ao Spark)
    2. Precisamos de **portabilidade**: qualquer SparkSession pode ler os Delta pelo caminho S3
    3. Um `DROP TABLE` acidental **não destrói** os dados
    4. Diferentes notebooks e membros da equipe podem acessar os mesmos dados sem depender de um metastore centralizado

---

## Resumo Visual

```
┌─────────────────────────────────────────────────────────┐
│                   TABELA GERENCIADA                     │
│                                                         │
│  CREATE TABLE t USING DELTA AS SELECT ...               │
│  df.write.saveAsTable("t")                              │
│                                                         │
│  ┌─────────────────┐    ┌──────────────────────┐        │
│  │   Catálogo      │───▶│  spark-warehouse/t/  │        │
│  │   (metadados)   │    │  (dados Delta)       │        │
│  └─────────────────┘    └──────────────────────┘        │
│                                                         │
│  DROP TABLE t  →  apaga metadados E dados ⚠️            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 TABELA NÃO GERENCIADA                   │
│                                                         │
│  CREATE TABLE t USING DELTA LOCATION 's3a://bronze/t/'  │
│  df.write.save("s3a://bronze/t/")                       │
│                                                         │
│  ┌─────────────────┐    ┌──────────────────────┐        │
│  │   Catálogo      │───▶│  s3a://bronze/t/     │        │
│  │   (metadados)   │    │  (dados Delta)       │        │
│  └─────────────────┘    └──────────────────────┘        │
│          │                        │                     │
│    DROP TABLE t                   │                     │
│    apaga apenas isto ──┘         dados permanecem ✔️    │
└─────────────────────────────────────────────────────────┘
```
