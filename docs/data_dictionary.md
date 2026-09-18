# Banking Data Pipeline --- Technical Data Dictionary

## 1. Purpose

This document defines the source entities, attributes, relationships,
data types, constraints, transformation rules, quality rules, lineage,
and analytical semantics used by the banking data pipeline.

The source of truth is the PostgreSQL OLTP database.

The downstream layers are:

``` text
PostgreSQL
    |
    v
Bronze
    |
    v
Silver
    |
    v
Gold
```

------------------------------------------------------------------------

## 2. Source System

The transactional source is:

``` text
Database: banking_oltp
DBMS: PostgreSQL 17
```

The source contains seven tables:

``` text
agencias
clientes
tipos_transacao
contas
cartoes
emprestimos
transacoes
```

The relational model is designed around customers, branches, accounts,
cards, loans, transaction types, and transactions.

------------------------------------------------------------------------

## 3. Entity Relationship Overview

``` text
                     +----------------+
                     |    agencias    |
                     +----------------+
                             |
                             | 1:N
                             v
                     +----------------+
                     |     contas     |
                     +----------------+
                       ^            |
                       |            | 1:N
                    N:1|            +----------+
                       |                       |
              +----------------+       +-------v--------+
              |    clientes    |       |    cartoes     |
              +----------------+       +----------------+
                    |
                    | 1:N
                    v
              +----------------+
              |  emprestimos   |
              +----------------+

contas
   |
   +-----------------------------+
   |                             |
   | 1:N                         | 1:N
   v                             v
transacoes                 transacoes
   |
   | N:1
   v
tipos_transacao
```

------------------------------------------------------------------------

# 4. Table: `agencias`

## Purpose

Represents banking branches.

## Columns

``` text
agencia_id
nome_agencia
cidade
```

### `agencia_id`

-   Logical type: integer.
-   Role: primary key.
-   Nullability: NOT NULL.
-   Uniqueness: unique by primary-key constraint.
-   Semantics: identifies one branch.

### `nome_agencia`

-   Logical type: text.
-   Nullability: NOT NULL.
-   Semantics: branch display name.

### `cidade`

-   Logical type: text.
-   Nullability: NOT NULL.
-   Semantics: city where the branch is located.

## Relationships

Referenced by:

``` text
contas.agencia_id -> agencias.agencia_id
```

------------------------------------------------------------------------

# 5. Table: `clientes`

## Purpose

Represents banking customers.

## Columns

``` text
cliente_id
nome
cpf
data_nascimento
```

### `cliente_id`

-   Logical type: integer.
-   Role: primary key.
-   Nullability: NOT NULL.
-   Uniqueness: unique.
-   Semantics: customer identifier.

### `nome`

-   Logical type: text.
-   Nullability: NOT NULL.
-   Semantics: synthetic customer name.

### `cpf`

-   Logical type: text.
-   Nullability: NOT NULL.
-   Uniqueness: unique.
-   Semantics: synthetic Brazilian CPF identifier.

The generator checks generated CPFs against existing records to avoid
collisions.

### `data_nascimento`

-   Logical type: date.
-   Nullability: NOT NULL.
-   Semantics: customer date of birth.
-   Silver representation: remains date-only.

------------------------------------------------------------------------

# 6. Table: `tipos_transacao`

## Purpose

Reference table containing transaction types.

## Columns

``` text
tipo_transacao_id
descricao
```

### `tipo_transacao_id`

-   Logical type: integer.
-   Role: primary key.
-   Semantics: transaction type identifier.

### `descricao`

-   Logical type: text.
-   Nullability: NOT NULL.
-   Semantics: human-readable transaction type.

The seeded transaction types are:

``` text
1 -> PIX
2 -> TED
3 -> DOC
4 -> SAQUE
5 -> DEPOSITO
```

The seed operation uses conflict-safe insertion so existing reference
records are not duplicated.

------------------------------------------------------------------------

# 7. Table: `contas`

## Purpose

Represents customer bank accounts.

## Columns

``` text
conta_id
cliente_id
agencia_id
saldo
```

### `conta_id`

-   Logical type: integer.
-   Role: primary key.
-   Semantics: account identifier.

### `cliente_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `clientes.cliente_id`.
-   Semantics: owner of the account.

### `agencia_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `agencias.agencia_id`.
-   Semantics: branch associated with the account.

### `saldo`

-   Logical type: NUMERIC(15,2).
-   Semantics: account balance.
-   Precision: 15 digits total.
-   Scale: 2 decimal places.

------------------------------------------------------------------------

# 8. Table: `cartoes`

## Purpose

Represents cards associated with bank accounts.

## Columns

``` text
cartao_id
conta_id
numero_cartao
tipo_cartao
```

### `cartao_id`

-   Logical type: integer.
-   Role: primary key.
-   Semantics: card identifier.

### `conta_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `contas.conta_id`.
-   Semantics: account associated with the card.

### `numero_cartao`

-   Logical type: text.
-   Uniqueness: unique.
-   Semantics: synthetic 16-digit card number.

The generator checks new card numbers against existing database values
before insertion.

### `tipo_cartao`

-   Logical type: text.
-   Semantics: card type.
-   Generated values:

``` text
DEBIT
CREDIT
```

Silver standardizes and protects card-number representation according to
its transformation rules.

------------------------------------------------------------------------

# 9. Table: `emprestimos`

## Purpose

Represents contracted customer loans.

## Columns

``` text
emprestimo_id
cliente_id
valor_contratado
parcelas
data_contrato
```

### `emprestimo_id`

-   Logical type: integer.
-   Role: primary key.
-   Semantics: loan identifier.

### `cliente_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `clientes.cliente_id`.
-   Semantics: customer responsible for the loan.

### `valor_contratado`

-   Logical type: NUMERIC(15,2).
-   Semantics: contracted loan amount.
-   Precision: 15 digits.
-   Scale: 2 decimal places.

### `parcelas`

-   Logical type: integer.
-   Constraint: greater than zero.
-   Semantics: number of loan installments.

### `data_contrato`

-   Logical type: date.
-   Semantics: loan contract date.
-   Silver representation: date-only.

------------------------------------------------------------------------

# 10. Table: `transacoes`

## Purpose

Represents financial transactions between accounts.

## Columns

``` text
transacao_id
conta_origem_id
conta_destino_id
tipo_transacao_id
valor
data_hora
```

### `transacao_id`

-   Logical type: integer.
-   Role: primary key.
-   Semantics: transaction identifier.

### `conta_origem_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `contas.conta_id`.
-   Semantics: source account.

### `conta_destino_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `contas.conta_id`.
-   Semantics: destination account.

### `tipo_transacao_id`

-   Logical type: integer.
-   Role: foreign key.
-   References: `tipos_transacao.tipo_transacao_id`.
-   Semantics: transaction classification.

### `valor`

-   Logical type: NUMERIC(15,2).
-   Semantics: financial transaction amount.
-   Precision: 15 digits.
-   Scale: 2 decimal places.

### `data_hora`

-   Logical type: timestamp.
-   Semantics: transaction event timestamp.
-   Silver representation: standardized datetime in UTC.

------------------------------------------------------------------------

# 11. Referential Integrity

The complete logical relationship set is:

``` text
contas.cliente_id
    -> clientes.cliente_id

contas.agencia_id
    -> agencias.agencia_id

cartoes.conta_id
    -> contas.conta_id

emprestimos.cliente_id
    -> clientes.cliente_id

transacoes.conta_origem_id
    -> contas.conta_id

transacoes.conta_destino_id
    -> contas.conta_id

transacoes.tipo_transacao_id
    -> tipos_transacao.tipo_transacao_id
```

These relationships exist at the OLTP level and are also explicitly
validated in Silver.

------------------------------------------------------------------------

# 12. Source Data Types

The main logical data categories are:

  Category                Examples
  ----------------------- --------------------------------------
  Identifier              `*_id`
  Text                    `nome`, `cidade`, `descricao`
  CPF                     `cpf`
  Card number             `numero_cartao`
  Date                    `data_nascimento`, `data_contrato`
  Datetime                `data_hora`
  Monetary                `saldo`, `valor`, `valor_contratado`
  Enumeration/reference   `tipo_cartao`, `tipo_transacao_id`

------------------------------------------------------------------------

# 13. Financial Data Standard

Financial columns use:

``` text
NUMERIC(15,2)
```

Relevant columns:

``` text
contas.saldo
emprestimos.valor_contratado
transacoes.valor
```

Silver preserves the two-decimal financial semantics.

The generator creates monetary values using integer cents and converts
them to `Decimal`, avoiding binary floating-point representation for
generated financial values.

------------------------------------------------------------------------

# 14. Date and Time Standard

Date-only fields:

``` text
clientes.data_nascimento
emprestimos.data_contrato
```

remain dates.

The transaction field:

``` text
transacoes.data_hora
```

is treated as a datetime.

The project interprets source timestamps using:

``` text
America/Sao_Paulo
```

and normalizes them to UTC.

Conceptual transformation:

``` text
2026-09-11 10:00:00
America/Sao_Paulo
        |
        v
2026-09-11 13:00:00 UTC
```

------------------------------------------------------------------------

# 15. Bronze Metadata

Every Bronze dataset receives:

``` text
_source_system
_ingestion_timestamp
_batch_id
```

### `_source_system`

Identifies the originating source system:

``` text
banking_oltp_postgres
```

### `_ingestion_timestamp`

Identifies when the extraction occurred.

### `_batch_id`

UUID identifying the extraction execution.

All seven tables produced by one Bronze execution share the same batch
ID.

------------------------------------------------------------------------

# 16. Bronze Physical Model

Bronze follows:

``` text
data/bronze/
└── <table>/
    └── ingestion_date=<YYYY-MM-DD>/
        └── batch_id=<UUID>/
            └── <table>.parquet
```

The batch metadata marker is:

``` text
data/bronze/_metadata/
└── ingestion_date=<YYYY-MM-DD>/
    └── batch_id=<UUID>/
        └── _SUCCESS
```

------------------------------------------------------------------------

# 17. Silver Data Model

Silver represents standardized and validated source entities.

The main transformations are:

``` text
Primary-key validation
Duplicate detection
Required-field validation
Null handling
CPF normalization
Card-number normalization
Card-number protection
Monetary normalization
Date normalization
Datetime normalization
Foreign-key validation
Transaction consistency validation
```

Silver output is partitioned by:

``` text
ingestion_date
batch_id
```

------------------------------------------------------------------------

# 18. Silver Quality Rules

## Primary keys

Every source entity requires:

``` text
non-null primary key
unique primary key
```

Invalid rows are rejected.

## Required fields

The following fields are required.

### `agencias`

``` text
agencia_id
nome_agencia
cidade
```

### `clientes`

``` text
cliente_id
nome
cpf
data_nascimento
```

### `tipos_transacao`

``` text
tipo_transacao_id
descricao
```

### `contas`

``` text
conta_id
cliente_id
agencia_id
saldo
```

### `cartoes`

``` text
cartao_id
conta_id
numero_cartao
tipo_cartao
```

### `emprestimos`

``` text
emprestimo_id
cliente_id
valor_contratado
parcelas
data_contrato
```

### `transacoes`

``` text
transacao_id
conta_origem_id
conta_destino_id
tipo_transacao_id
valor
data_hora
```

------------------------------------------------------------------------

# 19. Rejection Semantics

Invalid records are not silently discarded.

They are written to:

``` text
data/silver_rejects/
```

The quarantine layout is:

``` text
data/silver_rejects/
└── <table>/
    └── ingestion_date=<YYYY-MM-DD>/
        └── batch_id=<UUID>/
            └── rejected.parquet
```

Audit columns include:

``` text
_reject_reason
_rejected_at
```

Potential reasons include:

``` text
Null or duplicated primary key.
Required field is null.
Invalid foreign-key reference.
Invalid monetary value.
Invalid datetime.
Invalid transaction relationship.
```

------------------------------------------------------------------------

# 20. Data Lineage

The lineage of a field is conceptually:

``` text
PostgreSQL column
       |
       v
Extraction
       |
       v
Bronze Parquet
       |
       +--> audit metadata
       |
       v
Silver
       |
       +--> validation
       +--> standardization
       +--> deduplication
       |
       v
Gold
```

Bronze is the raw historical representation.

Silver is the trusted analytical source.

Gold contains derived business metrics rather than a direct copy of the
OLTP model.

------------------------------------------------------------------------

# 21. Gold Datasets

## `daily_transaction_volume`

Purpose:

Measure daily transaction activity.

Derived from:

``` text
transacoes.transacao_id
transacoes.valor
transacoes.data_hora
```

Metrics:

``` text
transaction count
financial volume
```

------------------------------------------------------------------------

## `daily_pix_transaction_volume`

Purpose:

Measure daily PIX activity.

Derived through:

``` text
transacoes
    JOIN
tipos_transacao
```

with:

``` text
descricao = PIX
```

Metrics:

``` text
PIX transaction count
PIX financial volume
```

------------------------------------------------------------------------

## `financial_volume_by_agency`

Purpose:

Measure transaction financial activity by branch.

Lineage:

``` text
transacoes
    |
    v
contas (origin account)
    |
    v
agencias
```

Metrics:

``` text
transaction count
financial volume
```

------------------------------------------------------------------------

## `transactions_per_customer`

Purpose:

Measure transaction activity associated with customers.

Lineage:

``` text
transacoes
    |
    v
contas (origin account)
    |
    v
clientes
```

Metric:

``` text
transaction count per customer
```

------------------------------------------------------------------------

## `average_balance_by_agency`

Purpose:

Measure account balance characteristics by agency.

Lineage:

``` text
contas
    |
    v
agencias
```

Metrics:

``` text
account count
average balance
```

------------------------------------------------------------------------

## `customers_with_loans`

Purpose:

Identify customers associated with loans and summarize their contracted
credit.

Lineage:

``` text
clientes
    JOIN
emprestimos
```

Metrics:

``` text
loan count
total contracted loan value
average installments
```

------------------------------------------------------------------------

## `loan_volume`

Purpose:

Provide an aggregate view of the loan portfolio represented by the
dataset.

Metrics:

``` text
loan count
total contracted loan value
average loan value
average installments
```

------------------------------------------------------------------------

# 22. Generator Data Volumes

Default configuration:

``` text
NUM_AGENCIAS=10
NUM_CLIENTES=1000
NUM_CONTAS=1200
NUM_CARTOES=900
NUM_EMPRESTIMOS=400
NUM_TRANSACOES=10000
```

These values represent the number of records generated per generator
execution, not necessarily the final database totals.

Because the current generator is incremental, repeated executions
accumulate records.

------------------------------------------------------------------------

# 23. Synthetic Identifier Rules

## CPF

Generated as an 11-digit synthetic string.

The generator verifies uniqueness against:

``` text
newly generated CPFs
+
existing database CPFs
```

## Card number

Generated as a 16-digit synthetic string.

The generator verifies uniqueness against:

``` text
newly generated card numbers
+
existing database card numbers
```

------------------------------------------------------------------------

# 24. Transaction Generation Rules

A generated transaction contains:

``` text
origin account
destination account
transaction type
value
timestamp
```

The destination account is regenerated when it is equal to the source
account.

Therefore:

``` text
conta_origem_id != conta_destino_id
```

for generated transactions.

Transaction values are generated using integer cents and represented as
`Decimal`.

Transaction timestamps are generated from 2024 through the current UTC
time during execution.

------------------------------------------------------------------------

# 25. Loan Generation Rules

Generated loans include:

``` text
customer
contracted value
installment count
contract date
```

Installment options are:

``` text
6
12
18
24
36
48
```

Contracted values are generated within the configured synthetic monetary
range.

Silver additionally enforces the business rule that:

``` text
parcelas > 0
```

------------------------------------------------------------------------

# 26. Card Data

Cards are associated with accounts:

``` text
cartoes.conta_id
    |
    v
contas.conta_id
```

Generated card types are:

``` text
DEBIT
CREDIT
```

Card numbers are synthetic.

The Silver layer protects the card representation so downstream
analytical datasets do not unnecessarily expose the full identifier.

------------------------------------------------------------------------

# 27. Source of Truth

The system of record hierarchy is:

``` text
PostgreSQL
    = source of truth

Bronze
    = raw historical extraction

Silver
    = validated and standardized source representation

Gold
    = derived analytical representation
```

Gold should never be treated as a replacement for the transactional
source.

------------------------------------------------------------------------

# 28. Batch Semantics

A batch represents one coherent processing event.

Example:

``` text
batch_id = A

Bronze
├── agencias
├── clientes
├── contas
├── cartoes
├── emprestimos
├── tipos_transacao
└── transacoes

Silver
├── agencias
├── clientes
├── contas
├── cartoes
├── emprestimos
├── tipos_transacao
└── transacoes

Gold
├── daily_transaction_volume
├── daily_pix_transaction_volume
├── financial_volume_by_agency
├── transactions_per_customer
├── average_balance_by_agency
├── customers_with_loans
└── loan_volume
```

A batch should not combine source tables from different ingestion
executions.

------------------------------------------------------------------------

# 29. Historical Retention Model

The pipeline uses batch-specific physical paths.

Therefore:

``` text
Batch A != Batch B
```

and:

``` text
Silver Batch A
```

is not overwritten by:

``` text
Silver Batch B
```

This supports:

-   reproducibility;
-   historical inspection;
-   reprocessing;
-   debugging;
-   lineage;
-   comparison between processing executions.

------------------------------------------------------------------------

# 30. Data Quality Test Coverage

The current automated tests include explicit quarantine behavior.

For example, a client record with:

``` text
cliente_id = NULL
```

is rejected from the clean Silver result.

The quarantine test verifies:

``` text
valid row
    -> Silver

invalid row
    -> silver_rejects/rejected.parquet
```

The test suite also validates the existence of:

``` text
_reject_reason
_rejected_at
```

------------------------------------------------------------------------

# 31. Analytical Semantics

The Gold layer is designed around business questions such as:

### Customer

-   How many transactions are associated with each customer?
-   Which customers have loans?

### Accounts

-   What is the average balance by agency?
-   How many accounts are associated with each branch?

### Transactions

-   What is the daily transaction volume?
-   What is the daily PIX volume?
-   What is the financial volume by agency?

### Loans

-   How many loans exist?
-   What is the total contracted loan volume?
-   What is the average loan value?
-   What is the average installment count?

------------------------------------------------------------------------

# 32. Future Data Extensions

The architecture allows additional analytical datasets to be added
without changing the OLTP source model.

Potential future Gold metrics documented by the project design include:

``` text
risk indicators
delinquency indicators
additional customer segmentation
additional transaction analysis
```

Such metrics should consume validated Silver data.

------------------------------------------------------------------------

# 33. Data Governance Principles

1.  Source data is preserved in Bronze.
2.  Silver is the quality boundary.
3.  Invalid records are explicitly quarantined.
4.  Gold contains derived analytical semantics.
5.  Batch IDs provide processing traceability.
6.  Sensitive configuration is externalized.
7.  Synthetic data is used for development.
8.  Historical processing outputs are partitioned.
9.  Referential integrity is validated before analytical use.
10. Data transformations are separated from source extraction.

------------------------------------------------------------------------

# 34. Summary

The banking data model is composed of:

``` text
agencias
clientes
tipos_transacao
contas
cartoes
emprestimos
transacoes
```

The pipeline transforms this transactional model into a layered
analytical system:

``` text
PostgreSQL
    |
    v
Bronze
    |
    v
Silver
    |
    v
Gold
```

The most important data-quality boundary is Silver.

The most important lineage mechanism is the batch ID.

The most important analytical boundary is that Gold consumes validated
Silver rather than raw Bronze data.
