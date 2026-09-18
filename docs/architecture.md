# Banking Data Pipeline --- Technical Architecture

## 1. Purpose

This document describes the technical architecture of the
`data-pipeline-repository` project, an end-to-end banking data pipeline
built to simulate the lifecycle of transactional financial data from an
OLTP source through analytical datasets.

The architecture is based on a Medallion-style data model:

``` text
Synthetic Data Generator
        |
        v
PostgreSQL OLTP
        |
        v
Extraction
        |
        v
Bronze
        |
        v
Silver
        |
        v
Gold
        |
        v
BI / Analytics
```

The project is designed for local reproducibility, deterministic
synthetic data generation, data-quality enforcement, historical batch
preservation, independent layer execution, automated testing, and
separation of responsibilities.

------------------------------------------------------------------------

## 2. Architectural Goals

The project has the following technical goals:

-   Provide a reproducible local banking environment.
-   Keep the transactional model relational and normalized.
-   Separate database schema creation from data generation.
-   Generate synthetic data without using real customer information.
-   Preserve extracted source data in an immutable-style Bronze history.
-   Associate all datasets from one extraction execution with a common
    batch identifier.
-   Validate and standardize data before analytical consumption.
-   Quarantine invalid records instead of silently propagating them.
-   Preserve Silver processing history so reprocessing does not
    overwrite previous batches.
-   Build business-oriented Gold datasets exclusively from validated
    Silver data.
-   Make each pipeline stage independently executable.
-   Centralize configuration and logging.
-   Keep secrets and generated data outside version control.
-   Validate code through Ruff, Mypy, and Pytest.

------------------------------------------------------------------------

## 3. Technology Stack

  Concern                      Technology
  ---------------------------- -------------------------
  Language                     Python 3.11
  Package/dependency manager   uv
  Synthetic data               Faker
  OLTP database                PostgreSQL 17
  Database administration      pgAdmin
  Containerization             Docker / Docker Compose
  Database driver              psycopg2
  Data processing              pandas
  Columnar storage             Apache Parquet
  Parquet engine               PyArrow
  Configuration                `.env`, `.env.example`
  Testing                      Pytest
  Linting                      Ruff
  Static typing                Mypy
  Version control              Git / GitHub
  Future/consumer layer        Power BI / Metabase

The project is constrained to Python `>=3.11,<3.12`.

------------------------------------------------------------------------

## 4. Repository Structure

The relevant project structure is:

``` text
data-pipeline-repository/
├── database/
│   ├── ddl/
│   │   └── 01_create_tables.sql
│   └── seeds/
│       └── 01_seed_transaction_types.sql
│
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
│
├── docs/
│   ├── architecture.md
│   └── data_dictionary.md
│
├── src/
│   ├── main.py
│   ├── config.py
│   │
│   ├── generator/
│   │   ├── generate_data.py
│   │   ├── helpers.py
│   │   ├── customers.py
│   │   ├── accounts.py
│   │   ├── cards.py
│   │   ├── loans.py
│   │   └── transactions.py
│   │
│   ├── extraction/
│   │   └── extract.py
│   │
│   ├── bronze/
│   │   └── bronze.py
│   │
│   ├── silver/
│   │   ├── config.py
│   │   ├── io.py
│   │   ├── silver.py
│   │   ├── transformations.py
│   │   └── validation.py
│   │
│   ├── gold/
│   │   └── gold.py
│   │
│   └── utils/
│       └── database.py
│
└── tests/
    ├── test_database.py
    ├── test_generator.py
    ├── test_silver_validation.py
    ├── test_silver_quarantine.py
    ├── test_silver_transformations.py
    └── test_silver_integration.py
```

Each package has a specific responsibility. The generator, extraction,
Bronze, Silver, and Gold layers should not duplicate business
responsibilities.

------------------------------------------------------------------------

## 5. Runtime Architecture

The main entry point is:

``` text
src/main.py
```

It provides a command-line interface through the `--stage` argument.

Supported stages:

``` text
generator
bronze
silver
gold
full
```

Examples:

``` bash
uv run python -m main --stage generator
uv run python -m main --stage bronze
uv run python -m main --stage silver
uv run python -m main --stage gold
uv run python -m main --stage full
```

The full execution order is:

``` text
Step 1/4 - Generator
Step 2/4 - Bronze
Step 3/4 - Silver
Step 4/4 - Gold
```

The orchestrator centralizes application logging and converts unhandled
stage failures into a non-zero process exit.

------------------------------------------------------------------------

## 6. Local Infrastructure

### 6.1 PostgreSQL

PostgreSQL runs inside Docker.

``` text
Container: banking-postgres
Image: postgres:17
Database: banking_oltp
User: banking_user
Internal port: 5432
Host port: 15432
```

The connection from the host is:

``` text
localhost:15432
        |
        v
Docker PostgreSQL:5432
```

The port is exposed on `15432` to avoid conflicts with another
PostgreSQL service running on the host.

### 6.2 pgAdmin

pgAdmin runs as a separate container:

``` text
localhost:5050
        |
        v
pgAdmin container
```

It is used for database inspection and Query Tool execution.

### 6.3 Persistence

The PostgreSQL service uses a Docker volume for database persistence.

This has an important operational consequence:

``` bash
docker compose down
```

does not remove the database volume.

Whereas:

``` bash
docker compose down -v
```

removes the volume and therefore destroys the current PostgreSQL state.

The latter should only be used deliberately when a clean database
initialization test is required.

------------------------------------------------------------------------

## 7. Configuration

Runtime configuration is centralized through environment variables.

Important PostgreSQL variables include:

``` text
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

Data-layer variables include:

``` text
DATA_DIR
BRONZE_DIR
SILVER_DIR
GOLD_DIR
```

Generator variables include:

``` text
FAKER_LOCALE
FAKER_SEED
NUM_AGENCIAS
NUM_CLIENTES
NUM_CONTAS
NUM_CARTOES
NUM_EMPRESTIMOS
NUM_TRANSACOES
```

Application configuration also includes logging and environment
information.

The real `.env` is intentionally excluded from Git. `.env.example`
provides a safe configuration template.

------------------------------------------------------------------------

## 8. Database Initialization

The PostgreSQL container mounts:

``` text
database/ddl/
    |
    v
/docker-entrypoint-initdb.d/
```

The schema definition is:

``` text
database/ddl/01_create_tables.sql
```

Transaction types are seeded separately through:

``` text
database/seeds/01_seed_transaction_types.sql
```

The DDL uses `CREATE TABLE IF NOT EXISTS`, which makes repeated
initialization attempts non-failing when tables already exist.

However, this does not perform schema migrations. If an existing table
differs from the SQL definition, `CREATE TABLE IF NOT EXISTS` does not
reconcile the differences.

The Docker PostgreSQL initialization scripts are executed automatically
when PostgreSQL initializes a new database volume.

A clean initialization test can be performed with:

``` bash
docker compose down -v
docker compose up -d
```

This is destructive because the PostgreSQL volume is removed.

------------------------------------------------------------------------

## 9. OLTP Data Model

The transactional source contains seven tables:

``` text
agencias
clientes
tipos_transacao
contas
cartoes
emprestimos
transacoes
```

The main relationships are:

``` text
agencias
    |
    v
contas <----- clientes
    |
    +----> cartoes
    |
    +----> transacoes <----- tipos_transacao

clientes
    |
    +----> emprestimos
```

Foreign keys enforce relational integrity in PostgreSQL.

The OLTP database is the source of truth for the pipeline.

------------------------------------------------------------------------

## 10. Synthetic Data Generation

The generator uses Faker with:

``` text
FAKER_LOCALE=pt_BR
FAKER_SEED=42
```

The default configured batch sizes are:

``` text
Agencies:       10
Customers:      1,000
Accounts:       1,200
Cards:          900
Loans:          400
Transactions:   10,000
```

The generator is modularized to avoid a monolithic implementation.

Responsibilities are separated as follows:

``` text
helpers.py
    |
    +-- CPF generation
    +-- card number generation
    +-- monetary values
    +-- transaction timestamps
    +-- next-ID calculation

customers.py
    |
    +-- customer generation

accounts.py
    |
    +-- account generation

cards.py
    |
    +-- card generation

loans.py
    |
    +-- loan generation

transactions.py
    |
    +-- transaction generation

generate_data.py
    |
    +-- orchestration
    +-- database connection
    +-- insertion order
    +-- logging
```

The current generator is incremental.

It calculates the next identifier using:

``` sql
SELECT COALESCE(MAX(id), 0) + 1
```

It also checks existing CPFs and card numbers before insertion.

Therefore, executing the generator multiple times adds another synthetic
dataset instead of clearing the existing database.

This behavior is important for understanding pipeline batch growth.

------------------------------------------------------------------------

## 11. Generator Insertion Order

The insertion order respects foreign-key dependencies:

``` text
1. agencias
2. clientes
3. tipos_transacao
4. contas
5. cartoes
6. emprestimos
7. transacoes
```

Conceptually:

``` text
Agencies
    |
    +------------------+
    |                  |
    v                  |
Accounts               |
    |                  |
    +--> Cards         |
    |                  |
    +--> Transactions  |
                       |
Customers --------------+
    |
    +--> Loans
```

The transaction type reference data is seeded before transactions are
generated.

------------------------------------------------------------------------

## 12. Extraction Layer

The extraction implementation is:

``` text
src/extraction/extract.py
```

The extraction layer reads the seven OLTP tables.

Its responsibilities are intentionally limited to:

1.  Validate requested source table names.
2.  Open or reuse a PostgreSQL connection.
3.  Execute SQL reads.
4.  Fetch records in batches.
5.  Convert results into pandas DataFrames.
6.  Return source data to the Bronze layer.
7.  Close connections owned by the extraction function.

The extraction layer does not perform analytical business logic.

This separation prevents source extraction from becoming coupled to
downstream transformations.

------------------------------------------------------------------------

## 13. Connection Management

The shared database utility is:

``` text
src/utils/database.py
```

It centralizes PostgreSQL connection creation.

The connection configuration includes:

``` text
host
port
database
user
password
connect_timeout
application_name
```

The application identifies itself to PostgreSQL using:

``` text
application_name=data-pipeline
```

Connection ownership is handled explicitly. When a caller provides an
existing connection, extraction can reuse it; otherwise the extraction
function creates and closes its own connection.

The `extract_all()` flow uses a shared connection for the complete
source extraction.

------------------------------------------------------------------------

## 14. Bronze Layer

The Bronze implementation is:

``` text
src/bronze/bronze.py
```

Bronze represents the raw historical extraction layer.

The data is persisted as Parquet.

The physical layout is:

``` text
data/
└── bronze/
    └── <table>/
        └── ingestion_date=<YYYY-MM-DD>/
            └── batch_id=<UUID>/
                └── <table>.parquet
```

For example:

``` text
data/bronze/transacoes/
└── ingestion_date=2026-09-18/
    └── batch_id=7c8640a4-2737-43e9-9eb7-45810b06d143/
        └── transacoes.parquet
```

------------------------------------------------------------------------

## 15. Bronze Audit Metadata

Every Bronze dataset receives:

``` text
_source_system
_ingestion_timestamp
_batch_id
```

The source identifier is:

``` text
banking_oltp_postgres
```

A single Bronze execution creates one common:

``` text
batch_id
ingestion_timestamp
ingestion_date
```

for all seven tables.

This allows the pipeline to identify the seven datasets as belonging to
the same extraction event.

------------------------------------------------------------------------

## 16. Batch Completeness

A Bronze batch is considered complete when all expected source tables
have a dataset for the same batch.

The Bronze layer also creates a success marker:

``` text
data/bronze/_metadata/
└── ingestion_date=<YYYY-MM-DD>/
    └── batch_id=<UUID>/
        └── _SUCCESS
```

The Silver layer identifies common batch IDs across the seven source
tables and selects the latest complete Bronze batch using the ingestion
timestamp.

This prevents mixing:

``` text
clientes from Batch A
+
contas from Batch B
+
transacoes from Batch C
```

during a single Silver processing run.

------------------------------------------------------------------------

## 17. Silver Layer

The Silver implementation is:

``` text
src/silver/
├── silver.py
├── io.py
├── validation.py
├── transformations.py
└── config.py
```

Silver is the trusted, standardized layer.

Its main responsibilities are:

-   Required-column validation.
-   Primary-key validation.
-   Duplicate detection.
-   Null validation.
-   CPF normalization.
-   Card-number normalization and masking.
-   Monetary-value normalization.
-   Date normalization.
-   Datetime normalization.
-   Foreign-key validation.
-   Transaction consistency validation.
-   Rejection of invalid records.
-   Persistent partitioned output.

The central principle is:

``` text
Raw source data must be validated before analytical consumption.
```

------------------------------------------------------------------------

## 18. Silver Processing Flow

The Silver flow is:

``` text
Find latest complete Bronze batch
              |
              v
Read all seven Bronze datasets
              |
              v
Validate required columns
              |
              v
Transform / standardize
              |
              v
Validate entity-specific rules
              |
       +------+------+
       |             |
       v             v
   Valid rows    Invalid rows
       |             |
       v             v
Silver output   silver_rejects
```

The Silver implementation processes the batch as a consistent unit.

------------------------------------------------------------------------

## 19. Silver Partitioning

Silver is physically partitioned by ingestion metadata:

``` text
data/silver/
└── <table>/
    └── ingestion_date=<YYYY-MM-DD>/
        └── batch_id=<UUID>/
            └── <table>.parquet
```

The metadata layer contains:

``` text
data/silver/_metadata/
└── ingestion_date=<YYYY-MM-DD>/
    └── batch_id=<UUID>/
        └── _SUCCESS
```

This design preserves previous Silver batches.

A new execution writes to a new batch directory instead of replacing the
previous batch.

Therefore:

``` text
Batch A
    |
    +--> Silver/ingestion_date=A/batch_id=A/

Batch B
    |
    +--> Silver/ingestion_date=B/batch_id=B/
```

Reprocessing does not inherently destroy Batch A.

------------------------------------------------------------------------

## 20. Silver Data Quality

### 20.1 Required columns

Each source entity has a defined set of required fields.

A dataset that does not contain required columns cannot be safely
transformed.

### 20.2 Primary keys

Every entity requires:

``` text
non-null primary key
unique primary key
```

Null or duplicate primary keys are rejected.

### 20.3 Null handling

Required fields cannot be null.

Invalid records are redirected to quarantine.

### 20.4 Foreign keys

The following relationships are validated:

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

Records containing invalid references are rejected.

### 20.5 Transaction validation

Transactions must reference valid source and destination accounts and a
valid transaction type.

The source and destination account must also represent distinct accounts
according to the generator's transaction-generation rule.

------------------------------------------------------------------------

## 21. Data Standardization

Silver standardizes source representations.

### CPF

CPF values are normalized to a consistent representation.

### Card number

Card numbers are normalized and protected according to the
transformation rules implemented by the Silver layer.

### Monetary values

Financial values are normalized to two-decimal monetary representations.

The source model uses:

``` text
NUMERIC(15,2)
```

for financial values.

### Dates

Date-only attributes remain dates.

Examples:

``` text
clientes.data_nascimento
emprestimos.data_contrato
```

### Datetimes

Transaction timestamps are handled as datetimes.

------------------------------------------------------------------------

## 22. Time Zone Standardization

The PostgreSQL transaction field is:

``` text
transacoes.data_hora
```

The project interprets the source timestamp as:

``` text
America/Sao_Paulo
```

and standardizes the resulting timestamp to UTC.

Conceptually:

``` text
PostgreSQL TIMESTAMP
        |
        v
America/Sao_Paulo
        |
        v
UTC
```

Example:

``` text
Source:
2026-09-11 10:00:00
America/Sao_Paulo

Silver:
2026-09-11 13:00:00 UTC
```

Date-only fields are not converted to UTC because they do not represent
a timestamp.

------------------------------------------------------------------------

## 23. Quarantine

Invalid records are persisted outside the clean Silver layer:

``` text
data/silver_rejects/
└── <table>/
    └── ingestion_date=<YYYY-MM-DD>/
        └── batch_id=<UUID>/
            └── rejected.parquet
```

Rejected records receive audit information including:

``` text
_reject_reason
_rejected_at
```

Example rejection reasons include:

``` text
Null or duplicated primary key.
Required field is null.
Invalid foreign-key reference.
Invalid monetary value.
Invalid datetime.
Invalid transaction relationship.
```

The quarantine mechanism prevents invalid records from silently reaching
Gold.

The project contains automated tests proving that rejected records are
persisted and that invalid client rows are excluded from the clean
result.

------------------------------------------------------------------------

## 24. Gold Layer

Gold is implemented in:

``` text
src/gold/gold.py
```

Gold is the business-oriented analytical layer.

A critical architectural rule is:

``` text
Gold consumes Silver.
Gold does not consume Bronze directly.
```

The Gold layer independently discovers the latest complete Silver batch
through Silver `_SUCCESS` markers.

This avoids coupling Gold to Bronze batch discovery.

------------------------------------------------------------------------

## 25. Gold Batch Discovery

Gold searches the Silver metadata structure:

``` text
data/silver/_metadata/
    |
    +--> ingestion_date=<date>/
          |
          +--> batch_id=<UUID>/
                |
                +--> _SUCCESS
```

The latest complete Silver batch is selected from this structure.

This guarantees that Gold operates on a Silver batch that completed
successfully.

------------------------------------------------------------------------

## 26. Gold Analytical Datasets

The current Gold implementation generates seven business-oriented
datasets.

### 26.1 Daily transaction volume

Dataset:

``` text
daily_transaction_volume
```

Metrics include:

-   transaction date;
-   transaction count;
-   total financial volume.

The transaction datetime is normalized to a UTC date before aggregation.

### 26.2 Daily PIX transaction volume

Dataset:

``` text
daily_pix_transaction_volume
```

Transactions are joined with transaction types and filtered to:

``` text
PIX
```

Metrics include:

-   transaction date;
-   PIX transaction count;
-   PIX financial volume.

### 26.3 Financial volume by agency

Dataset:

``` text
financial_volume_by_agency
```

Transactions are associated with the origin account and its agency.

Metrics include:

-   agency;
-   transaction count;
-   financial volume.

### 26.4 Transactions per customer

Dataset:

``` text
transactions_per_customer
```

Origin accounts are associated with customers.

The dataset measures transaction counts per customer.

### 26.5 Average balance by agency

Dataset:

``` text
average_balance_by_agency
```

Accounts are grouped by agency.

Metrics include:

-   account count;
-   average balance.

### 26.6 Customers with loans

Dataset:

``` text
customers_with_loans
```

Customers are joined with loans.

Metrics include:

-   customer identity;
-   loan count;
-   total contracted loan value;
-   average installments.

### 26.7 Loan volume

Dataset:

``` text
loan_volume
```

This provides overall loan metrics such as:

-   loan count;
-   total contracted value;
-   average loan value;
-   average number of installments.

Risk and delinquency indicators remain a possible future analytical
extension.

------------------------------------------------------------------------

## 27. Gold Output

Gold datasets are also associated with the processing batch.

Conceptually:

``` text
data/gold/
└── <dataset>/
    └── ingestion_date=<YYYY-MM-DD>/
        └── batch_id=<UUID>/
            └── <dataset>.parquet
```

The output is therefore traceable to the Silver batch used as input.

------------------------------------------------------------------------

## 28. Data Lineage

The complete lineage is:

``` text
Faker
  |
  v
PostgreSQL OLTP
  |
  | source
  v
Extraction
  |
  v
Bronze
  |
  | raw + audit metadata
  v
Silver
  |
  | validation
  | standardization
  | deduplication
  | referential integrity
  | quarantine
  v
Gold
  |
  | business aggregations
  v
BI / Analytics
```

The semantic responsibility of each layer is:

``` text
PostgreSQL = transactional source of truth
Bronze      = historical raw extraction
Silver      = validated and standardized data
Gold        = business-oriented analytical datasets
```

------------------------------------------------------------------------

## 29. Reprocessing Model

The pipeline uses batch-aware storage.

A new execution receives a new UUID:

``` text
batch_id
```

Therefore, a sequence can look like:

``` text
Batch A
Bronze A
Silver A
Gold A

Batch B
Bronze B
Silver B
Gold B
```

The previous batch directories remain available.

This prevents the previous Silver result from being overwritten by a new
processing run.

The current generator is also incremental, so each generator execution
can create additional source records before a subsequent extraction.

------------------------------------------------------------------------

## 30. Error Handling

The application uses logging and exception propagation.

At the top level:

``` text
main.py
    |
    +--> stage execution
    |
    +--> exception
             |
             v
       logger.exception(...)
             |
             v
       return code 1
```

A successful execution returns:

``` text
0
```

A failed pipeline stage returns:

``` text
1
```

This behavior makes the command-line pipeline suitable for later
integration with an external scheduler.

------------------------------------------------------------------------

## 31. Logging

Logging is configured centrally by `src/main.py`.

The configured format is:

``` text
timestamp | level | logger | message
```

The log level is controlled through:

``` text
LOG_LEVEL
```

Individual layers use module-level loggers rather than printing directly
to stdout.

This allows consistent operational diagnostics.

------------------------------------------------------------------------

## 32. Testing Strategy

The project uses Pytest for automated testing.

The test suite covers areas including:

-   database behavior;
-   generator behavior;
-   Silver validation;
-   Silver quarantine;
-   Silver transformations;
-   Silver integration.

The quarantine tests verify:

``` text
invalid row
    |
    v
quarantine
    |
    v
rejected.parquet
```

and confirm that invalid rows are excluded from the clean result.

The latest validated test suite contains:

``` text
43 passed
```

------------------------------------------------------------------------

## 33. Static Analysis and Code Quality

The project uses:

``` bash
uv run ruff check src
uv run mypy src
uv run pytest
```

The latest known validation state was:

``` text
Ruff: PASS
Mypy: PASS
Pytest: 43 passed
```

Mypy is configured with:

``` text
mypy_path = "src"
explicit_package_bases = true
```

Ruff uses a maximum line length of:

``` text
100
```

------------------------------------------------------------------------

## 34. Reproducibility

The project is reproducible through:

-   Docker;
-   Docker Compose;
-   pinned Python major/minor compatibility;
-   uv dependency management;
-   `.env.example`;
-   Faker seed;
-   deterministic project structure;
-   version-controlled source code.

The synthetic generator seed is:

``` text
FAKER_SEED=42
```

This makes the generation process reproducible when the same source
state and generation conditions are used.

------------------------------------------------------------------------

## 35. Security and Data Protection

The project is intended to operate with synthetic banking data.

The following must not be committed:

``` text
.env
data/
*.parquet
*.csv
.venv/
logs/
cache directories
```

The `.gitignore` explicitly protects generated and local-only artifacts.

Database credentials are supplied through environment variables rather
than hard-coded into source modules.

Sensitive customer-like values are synthetic.

------------------------------------------------------------------------

## 36. Operational Commands

### Start infrastructure

``` bash
docker compose up -d
```

### Check containers

``` bash
docker compose ps
```

### Execute generator

``` bash
uv run python -m main --stage generator
```

### Execute Bronze

``` bash
uv run python -m main --stage bronze
```

### Execute Silver

``` bash
uv run python -m main --stage silver
```

### Execute Gold

``` bash
uv run python -m main --stage gold
```

### Execute everything

``` bash
uv run python -m main --stage full
```

### Run tests

``` bash
uv run pytest
```

### Run linting

``` bash
uv run ruff check src
```

### Run type checking

``` bash
uv run mypy src
```

### Stop infrastructure without deleting data

``` bash
docker compose down
```

### Remove infrastructure and PostgreSQL volume

``` bash
docker compose down -v
```

Use the final command only when database destruction is intentional.

------------------------------------------------------------------------

## 37. Architectural Principles

1.  Database structure is separate from synthetic data generation.
2.  OLTP responsibilities are separated from analytical processing.
3.  Extraction does not contain business transformations.
4.  Bronze preserves source history.
5.  Batch IDs identify coherent ingestion executions.
6.  Silver validates before analytical consumption.
7.  Invalid Silver records are quarantined.
8.  Silver history is preserved by batch.
9.  Gold consumes validated Silver.
10. Gold independently verifies the latest complete Silver batch.
11. Configuration is externalized.
12. Secrets remain outside version control.
13. Each stage can run independently.
14. Logging is centralized.
15. Automated tests are part of the delivery process.
16. Static analysis is performed before final delivery.

------------------------------------------------------------------------

## 38. Current End-to-End State

The pipeline has been validated end-to-end using:

``` bash
uv run python -m main --stage full
```

The execution sequence successfully completed:

``` text
Generator
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

The latest successful full execution generated Gold datasets for:

``` text
daily_transaction_volume
daily_pix_transaction_volume
financial_volume_by_agency
transactions_per_customer
average_balance_by_agency
customers_with_loans
loan_volume
```

This confirms that the implemented architecture is executable as a
complete local pipeline rather than only as isolated modules.
