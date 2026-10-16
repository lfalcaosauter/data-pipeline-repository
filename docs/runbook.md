# Runbook Operacional — Banking Data Pipeline

## 1. Objetivo

Este documento descreve os procedimentos operacionais para **executar, validar, reprocessar e diagnosticar** o Banking Data Pipeline, de forma que qualquer desenvolvedor ou operador consiga reproduzir o ambiente.

O pipeline segue a arquitetura Medallion, com orquestração e modelagem analítica:

```text
Generator
    ↓
PostgreSQL OLTP
    ↓
Extraction
    ↓
Bronze (Parquet)
    ↓
Silver (Parquet validado + quarentena)
    ↓
Gold (Python)  /  dbt (staging, dimensões e fatos)
    ↓
Grafana / Metabase

Apache Airflow orquestra as etapas (DAG banking_pipeline).
```

---

## 2. Pré-requisitos

### 2.1 Software

- Python 3.11 (`>=3.11,<3.12`)
- uv
- Docker e Docker Compose (Docker Desktop em execução)
- Git
- dbt (com adaptador PostgreSQL), caso seja executado fora do container

> **A confirmar:** se o dbt é instalado pelo `uv sync` (dependência no `pyproject.toml`) ou executado dentro do container do Airflow.

O PostgreSQL 17 roda em container; não é necessário instalá-lo na máquina.

### 2.2 Bibliotecas Python principais

pandas, pyarrow, psycopg2, Faker, python-dotenv, pytest, Ruff e MyPy.

---

## 3. Estrutura do projeto

```text
data-pipeline-repository/
├── airflow/
│   ├── dags/            # banking_pipeline.py
│   ├── logs/
│   └── plugins/
├── configs/
├── database/
│   ├── ddl/01_create_tables.sql
│   └── seeds/01_seed_transaction_types.sql
├── dbt/
│   ├── models/
│   ├── tests/
│   └── profiles.yml
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── runbook.md
│   └── testing.md
├── src/
│   ├── bronze/
│   ├── extraction/
│   ├── generator/
│   ├── gold/
│   ├── silver/
│   ├── utils/
│   ├── config.py
│   └── main.py
├── tests/
├── docker-compose.yml
├── .env / .env.example
├── pyproject.toml
└── uv.lock
```

---

## 4. Configuração inicial

```bash
cp .env.example .env     # ajuste as credenciais localmente
uv sync                  # instala as dependências
uv run python --version  # deve ser 3.11.x
```

Variáveis principais: `POSTGRES_*`, `PGADMIN_*`, `FAKER_LOCALE`, `FAKER_SEED`, `NUM_*`, `LOG_LEVEL`, `TIMEZONE` e os diretórios de dados (`DATA_DIR`, `BRONZE_DIR`, `SILVER_DIR`, `GOLD_DIR`).

O `.env` nunca deve ser versionado.

---

## 5. Subir a infraestrutura

```bash
docker compose up -d
docker compose ps
```

| Serviço | Endereço local | Finalidade |
|---|---|---|
| PostgreSQL | `localhost:15432` | Banco transacional (container `banking-postgres`, porta interna 5432) |
| pgAdmin | http://localhost:5050 | Administração do banco |
| Airflow | http://localhost:8080 | Orquestração |
| Grafana | http://localhost:3000 | Dashboards |
| Metabase | http://localhost:3001 | Exploração e visualização |

Confirme portas e nomes de serviço no `docker-compose.yml`. Antes de executar o pipeline, o PostgreSQL deve estar **saudável** (`healthy` em `docker compose ps`).

Na primeira subida (volume novo), o DDL e o seed dos tipos de transação são executados automaticamente.

---

## 6. Executar o pipeline Python

Execute sempre a partir da raiz do repositório.

| Etapa | Comando | O que faz |
|---|---|---|
| Generator | `uv run python -m main --stage generator` | Insere dados sintéticos no PostgreSQL |
| Bronze | `uv run python -m main --stage bronze` | Extrai as 7 tabelas para Parquet com um novo `batch_id` |
| Silver | `uv run python -m main --stage silver` | Valida e padroniza o último batch completo da Bronze |
| Gold | `uv run python -m main --stage gold` | Gera os datasets analíticos a partir do último batch completo da Silver |
| Completo | `uv run python -m main --stage full` | Generator → Bronze → Silver → Gold |

Pontos de atenção:

- **O Generator é incremental.** Cada execução adiciona novos registros; ela não limpa o banco. Executá-lo várias vezes aumenta o volume dos batches seguintes.
- O `main.py` retorna código de saída diferente de zero se uma etapa falhar. Verifique com `echo $?` (Linux/macOS) ou `$LASTEXITCODE` (PowerShell).

### 6.1 Onde ficam os dados

```text
data/
├── bronze/
│   ├── <tabela>/ingestion_date=YYYY-MM-DD/batch_id=<UUID>/<tabela>.parquet
│   └── _metadata/ingestion_date=YYYY-MM-DD/batch_id=<UUID>/_SUCCESS
├── silver/
│   ├── <tabela>/ingestion_date=YYYY-MM-DD/batch_id=<UUID>/<tabela>.parquet
│   └── _metadata/ingestion_date=YYYY-MM-DD/batch_id=<UUID>/_SUCCESS
├── silver_rejects/
│   └── <tabela>/ingestion_date=YYYY-MM-DD/batch_id=<UUID>/rejected.parquet
└── gold/
    └── <dataset>/ingestion_date=YYYY-MM-DD/batch_id=<UUID>/<dataset>.parquet
```

---

## 7. Executar o dbt

```bash
dbt run  --project-dir dbt --profiles-dir dbt
dbt test --project-dir dbt --profiles-dir dbt
```

- O dbt depende de um `profiles.yml` válido e do banco de destino disponível.
- Os modelos são materializados no schema `dbt_dev` (ambiente de desenvolvimento).
- Para um único modelo e seus dependentes: `dbt run --select fato_transacao+ --project-dir dbt --profiles-dir dbt`.

> **A confirmar:** de qual origem os modelos `stg_*` leem (tabelas do OLTP, ou dados da Silver carregados no PostgreSQL) e como essa carga é feita.

---

## 8. Apache Airflow

- Interface: http://localhost:8080
- DAG principal: `banking_pipeline` (`airflow/dags/banking_pipeline.py`)
- Agendamento: diário, `0 6 * * *` (o horário efetivo depende do fuso configurado no Airflow)

### Procedimento de execução manual

1. Acesse a interface e localize `banking_pipeline`.
2. Despause a DAG, se necessário.
3. Dispare uma execução (*Trigger DAG*).
4. Acompanhe o estado das tarefas na visão de grafo e abra os logs de qualquer tarefa com falha.

### Logs

```bash
docker compose logs --tail=100 airflow-scheduler
docker compose logs --tail=100 airflow-dag-processor
```

> **Importante:** dentro da rede Docker, o PostgreSQL é acessado pelo hostname do serviço e pela porta interna (`banking-postgres:5432`), **não** por `localhost:15432`. Configure as conexões do Airflow e do dbt de acordo com onde cada processo roda.

> **A confirmar:** lista de tarefas da DAG e suas dependências (por exemplo, se executa generator, bronze, silver, gold e dbt em sequência).

---

## 9. Visualização

- **Grafana** (http://localhost:3000): dashboards sobre transações e empréstimos.
- **Metabase** (http://localhost:3001): exploração e dashboards; conecte ao PostgreSQL e aos modelos do schema `dbt_dev`.
- **pgAdmin** (http://localhost:5050): consultas e inspeção do banco.

As consultas de negócio de referência estão em `business_queries.sql` e usam os modelos dbt (`dbt_dev.fato_transacao`, `dbt_dev.fato_emprestimo`, dimensões).

---

## 10. Validação pós-execução

### 10.1 Bronze

```bash
ls data/bronze/_metadata/*/          # deve existir um batch_id com _SUCCESS
```

Todas as 7 tabelas devem ter um arquivo Parquet para o mesmo `batch_id`.

### 10.2 Silver

```bash
ls data/silver/_metadata/*/          # marcador _SUCCESS do último batch
ls data/silver_rejects/              # existem rejeitados?
```

Se houver registros em `silver_rejects`, abra o `rejected.parquet` e verifique as colunas `_reject_reason` e `_rejected_at` para entender a causa.

### 10.3 Gold

Confirme que os 7 datasets existem para o `batch_id` da Silver utilizada:
`daily_transaction_volume`, `daily_pix_transaction_volume`, `financial_volume_by_agency`, `transactions_per_customer`, `average_balance_by_agency`, `customers_with_loans` e `loan_volume`.

### 10.4 Banco e dbt

```sql
SELECT COUNT(*) FROM transacoes;                       -- OLTP
SELECT COUNT(*) FROM dbt_dev.fato_transacao;           -- dbt
```

Os volumes do dbt devem ser coerentes com a origem utilizada. Diferenças grandes podem indicar registros rejeitados na Silver ou uma execução do dbt desatualizada.

---

## 11. Reprocessamento

- **Silver e Gold não sobrescrevem batches anteriores.** Cada execução cria um novo `batch_id`.
- Para reprocessar a partir da Bronze atual: `uv run python -m main --stage silver` e depois `--stage gold`.
- Para uma nova extração: `--stage bronze` (novo batch) e depois Silver e Gold.
- Execute o dbt novamente após reprocessar, caso os modelos dependam dos dados novos.
- Batches antigos permanecem em disco; remova-os manualmente apenas se for realmente necessário.

---

## 12. Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| Porta `15432`, `5050`, `8080`, `3000` ou `3001` em uso | Outro serviço usa a porta | Altere a porta no `.env`/compose ou pare o outro serviço |
| Erro de conexão com o PostgreSQL | Container não saudável ou credenciais erradas | `docker compose ps`, `docker compose logs --tail=100 banking-postgres`; confira o `.env` |
| `ModuleNotFoundError` ao rodar `-m main` | Execução fora da raiz ou ambiente sem `uv sync` | Rode da raiz do repositório e execute `uv sync` |
| Alterei o DDL e nada mudou | Scripts de init só rodam com volume vazio | Aplique a alteração manualmente ou recrie o volume (**destrutivo**, ver seção 13) |
| Silver não encontra batch | Bronze não rodou ou não tem `_SUCCESS` | Execute `--stage bronze` e confira `data/bronze/_metadata` |
| Gold não encontra batch | Silver não concluiu (sem `_SUCCESS`) | Execute `--stage silver` e confira `data/silver/_metadata` |
| Muitos registros em `silver_rejects` | Dados inconsistentes na origem | Analise `_reject_reason` no `rejected.parquet` |
| Volume cresce a cada execução | Generator é incremental | Comportamento esperado; recrie o banco se precisar de um estado limpo |
| DAG não aparece no Airflow | Erro de importação na DAG | `docker compose logs --tail=100 airflow-dag-processor` |
| Tarefa do Airflow não conecta ao banco | Uso de `localhost:15432` dentro do container | Use o hostname do serviço e a porta interna 5432 |
| dbt falha ao conectar | `profiles.yml` ou credenciais incorretos | Revise o perfil e o destino (host, porta, schema) |
| Metabase: `Failed to fetch` no login | Serviço ainda iniciando ou com erro | `docker compose ps`; `docker compose logs --tail=100 banking-metabase`; `docker compose restart banking-metabase`. Não redefina senha antes de verificar o serviço |
| Etapa retorna código ≠ 0 | Exceção na etapa | Leia o log (`LOG_LEVEL=DEBUG` para mais detalhes) |

---

## 13. Operações destrutivas

```bash
docker compose down      # para os serviços, preserva os volumes
docker compose down -v   # REMOVE os volumes (dados do PostgreSQL e das ferramentas)
```

Use `down -v` somente quando quiser deliberadamente um ambiente limpo (por exemplo, para testar a inicialização do zero). Em seguida, `docker compose up -d` recria o banco com o DDL e o seed.

Apagar o diretório `data/` remove Bronze, Silver, quarentena e Gold locais; eles podem ser regenerados pelo pipeline.

---

## 14. Checklist antes de um commit

```bash
uv run ruff check .
uv run mypy src
uv run pytest
dbt test --project-dir dbt --profiles-dir dbt
```

Confirme também que `.env`, `data/` e arquivos `*.parquet` não estão no `git status`.