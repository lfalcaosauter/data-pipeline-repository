# Runbook Operacional — Banking Data Pipeline

## 1. Objetivo

Este documento descreve os procedimentos operacionais para executar,
validar, reprocessar e diagnosticar o Banking Data Pipeline.

O pipeline implementa um fluxo de dados baseado em arquitetura Medallion:

PostgreSQL OLTP
    ↓
Extraction
    ↓
Bronze
    ↓
Silver
    ↓
Gold
    ↓
BI / Analytics

O objetivo deste runbook é permitir que qualquer desenvolvedor ou
operador consiga executar o projeto de forma reproduzível.

---

# 2. Pré-requisitos

## 2.1 Software

O ambiente requer:

- Python 3.11
- uv
- Docker
- Docker Compose
- PostgreSQL 17
- Git

A aplicação Python utiliza principalmente:

- pandas
- pyarrow
- psycopg2
- Faker
- python-dotenv
- pytest
- Ruff
- MyPy

---

# 3. Estrutura do projeto

```text
data-pipeline-repository/
│
├── database/
│   ├── ddl/
│   │   └── 01_create_tables.sql
│   │
│   └── seeds/
│       └── 01_seed_transaction_types.sql
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── runbook.md
│   └── testing.md
│
├── src/
│   ├── bronze/
│   ├── extraction/
│   ├── generator/
│   ├── gold/
│   ├── silver/
│   ├── utils/
│   ├── config.py
│   └── main.py
│
├── tests/
│
├── docker-compose.yml
├── .env
├── .env.example
├── pyproject.toml
└── uv.lock