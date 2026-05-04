# Modelo entidade-relacionamento — BibliotecaDb

O esquema **BibliotecaDb** no Microsoft SQL Server constitui a fonte das relações extraídas nos notebooks `00` e `01`. As secções seguintes apresentam, primeiro, a entidade de referência **`dbo_Categoria`** (utilizada nos exemplos de DML na Bronze) e, em seguida, o modelo global com as restantes tabelas do domínio da biblioteca.

## Entidade de referência: `dbo_Categoria`

A tabela `dbo_Categoria` classifica os registos de livros na aplicação de exemplo. Na camada Bronze, após o notebook `02`, acrescentam-se colunas de auditoria (`_bronze_loaded_at`, `_bronze_source_file`), mantendo-se a chave primária `id_categoria`.

```mermaid
erDiagram
    dbo_Categoria {
        int id_categoria PK
        string nome
        string descricao
    }
```

## Modelo global do domínio

O diagrama abaixo resume entidades, chaves e relacionamentos utilizados no pipeline até à Bronze.

```mermaid
erDiagram
    dbo_Categoria {
        int id_categoria PK
        string nome
        string descricao
    }
    dbo_Autor {
        int id_autor PK
        string nome
        string nacionalidade
        date data_nascimento
    }
    dbo_Livro {
        int id_livro PK
        string titulo
        string isbn
        int ano_publicacao
        int id_categoria FK
        int id_autor FK
    }
    dbo_Membro {
        int id_membro PK
        string nome
        string email
        string telefone
        date data_cadastro
    }
    dbo_Emprestimo {
        int id_emprestimo PK
        int id_livro FK
        int id_membro FK
        date data_emprestimo
        date data_devolucao_prevista
        date data_devolucao_real
        string status
    }
    dbo_Multa {
        int id_multa PK
        int id_emprestimo FK
        decimal valor
        boolean pago
        timestamp data_geracao
    }

    dbo_Categoria ||--o{ dbo_Livro : classifica
    dbo_Autor ||--o{ dbo_Livro : autoria
    dbo_Livro ||--o{ dbo_Emprestimo : exemplar
    dbo_Membro ||--o{ dbo_Emprestimo : tomador
    dbo_Emprestimo ||--o{ dbo_Multa : penalidade
```

As mesmas entidades aparecem como pastas Delta em `s3a://bronze/dbo_*` após o notebook `02_landing_to_bronze_delta.ipynb`, com colunas extras de auditoria na Bronze.
