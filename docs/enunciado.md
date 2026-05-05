# Enunciado e conformidade (Trabalho 2)

Esta página alinha a documentação e o repositório ao enunciado da atividade **Apache Spark com MinIO e SQL** (ciclo de vida e pipeline de dados), servindo de roteiro de entrega e revisão.

## Escopo em relação ao Trabalho 1

O Trabalho 2 **complementa** o Trabalho 1, mas é desenvolvido em **repositório GitHub distinto**, com **README** e **MkDocs** próprios — tal como pedido no enunciado. No **Trabalho 1**, em geral, pede-se materialização em **Delta Lake** e **Apache Iceberg**; no **Trabalho 2** a conversão é **apenas para Delta Lake** (não é necessário Iceberg neste laboratório).

## Repositório modelo

O desenvolvimento segue o repositório de referência:

**[jlsilva01/spark-delta-minio-sqlserver](https://github.com/jlsilva01/spark-delta-minio-sqlserver)**

Use-o como guia de estrutura, integração Spark + Delta + MinIO e boas práticas.

## Checklist do enunciado

| # | Requisito | Onde está coberto no projeto |
|---|-----------|------------------------------|
| 1 | Extrair os dados de **todas** as tabelas da base escolhida (relacional ou não relacional) e gravar no bucket **`landing-zone`** em **CSV** (relacional) ou **JSON** (não relacional). | Notebooks `00` e `01`; formato **CSV** por ser **SQL Server** relacional (`BibliotecaDb`). |
| 2 | Ler os ficheiros da `landing-zone` e gravar em **Delta Lake** no bucket **`bronze`**. | Notebook `02_landing_to_bronze_delta.ipynb`; páginas [Arquitetura Medalhão](arquitetura_medallion.md) e [Camada Bronze](camada_bronze.md). |
| 3 | Reproduzir as três operações de **DML** (**INSERT**, **UPDATE**, **DELETE**) do trabalho anterior sobre tabelas Delta na **bronze** (não obrigatório usar todas as tabelas). | Notebook `dml_bronze.ipynb`; secção DML em [Camada Bronze](camada_bronze.md). |
| 4 | Analisar diferenças entre tabelas **gerenciadas** e **não gerenciadas** nos dois laboratórios e **discutir em aula**. | [Tabelas gerenciadas vs não gerenciadas](tabelas_gerenciadas_vs_nao_gerenciadas.md), incluindo a secção sobre **Trabalho 1 e Trabalho 2**. |
| 5 | Trabalho 2 em **novo repositório** no GitHub (separado do Trabalho 1). | Política de entrega; este repositório é dedicado ao T2. |
| 6 | Utilizar o [repositório modelo](https://github.com/jlsilva01/spark-delta-minio-sqlserver) como base. | Estrutura e stack alinhadas ao exemplo. |
| 7 | **Sem** conversão para **Apache Iceberg** no Trabalho 2; apenas **Delta Lake**. Repositórios, pastas, bibliotecas, README e MkDocs **separados** entre T1 e T2. | Pipeline documentado só com **Delta**; MkDocs e README deste repo específicos do T2. |

## Prazo

A data de entrega indicada no material da disciplina foi **06/05** (confirmar no aviso oficial da turma em caso de alteração).

## Ligações úteis

- [Início — visão geral do pipeline](index.md)
- [Modelo ER (BibliotecaDb)](modelo_er_biblioteca.md)
