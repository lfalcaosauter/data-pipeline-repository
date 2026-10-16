# Data Pipeline Repository

Pipeline de Engenharia de Dados de ponta a ponta para um domínio bancário, desenvolvido com Python, PostgreSQL, Docker, Apache Airflow e dbt.

O projeto simula um ambiente de dados bancários: gera dados sintéticos, armazena-os em um PostgreSQL transacional, extrai para a camada Bronze, valida e padroniza na camada Silver, produz conjuntos analíticos na camada Gold (Python e dbt), orquestra tudo com Apache Airflow e disponibiliza os dados para exploração no Grafana e no Metabase.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Arquitetura](#arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Início Rápido](#início-rápido)
- [Configuração de Ambiente](#configuração-de-ambiente)
- [Infraestrutura com Docker](#infraestrutura-com-docker)
- [Banco de Dados](#banco-de-dados)
- [Generator](#generator)
- [Ponto de Entrada do Pipeline](#ponto-de-entrada-do-pipeline)
- [Camada Bronze](#camada-bronze)
- [Camada Silver](#camada-silver)
- [Camada Gold](#camada-gold)
- [Modelagem Analítica com dbt](#modelagem-analítica-com-dbt)
- [Orquestração com Apache Airflow](#orquestração-com-apache-airflow)
- [Visualização e Exploração de Dados](#visualização-e-exploração-de-dados)
- [Testes e Qualidade de Código](#testes-e-qualidade-de-código)
- [Logs e Tratamento de Erros](#logs-e-tratamento-de-erros)
- [Armazenamento e Reprodutibilidade](#armazenamento-e-reprodutibilidade)
- [Segurança e Dados Sensíveis](#segurança-e-dados-sensíveis)
- [Documentação Complementar](#documentação-complementar)
- [Princípios de Projeto](#princípios-de-projeto)
- [Status do Projeto](#status-do-projeto)

---

## Visão Geral

O projeto tem como objetivos:

- Gerar dados bancários sintéticos com Faker.
- Armazenar os dados operacionais em PostgreSQL.
- Extrair os dados e preservá-los, de forma bruta e histórica, na camada Bronze.
- Validar, limpar e padronizar os dados na camada Silver, com quarentena de registros inválidos.
- Disponibilizar conjuntos de dados analíticos na camada Gold.
- Gerenciar transformações SQL e testes de dados com dbt.
- Orquestrar as etapas do pipeline com Apache Airflow.
- Explorar e visualizar os dados com Grafana e Metabase.
- Executar todo o ambiente local com Docker Compose.
- Garantir qualidade com testes automatizados, Ruff e MyPy.

O pipeline pode ser executado por etapa individual ou de ponta a ponta, por um único ponto de entrada (`src/main.py`) ou pelo Airflow.

---

## Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python 3.11 | Geração, extração e processamento dos dados |
| PostgreSQL 17 | Armazenamento dos dados operacionais |
| Docker e Docker Compose | Containerização e gerenciamento do ambiente local |
| Apache Airflow | Orquestração e monitoramento das tarefas |
| dbt | Modelagem analítica e testes de dados |
| Pandas | Manipulação e transformação de dados |
| PyArrow | Processamento de arquivos Parquet |
| Faker | Geração de dados sintéticos |
| Psycopg2 | Conexão Python com PostgreSQL |
| Pytest | Testes automatizados |
| Ruff | Linting e análise estática |
| MyPy | Verificação estática de tipos |
| uv | Gerenciamento de dependências Python |
| Grafana | Dashboards e indicadores |
| Metabase | Exploração de dados e criação de visualizações |
| pgAdmin | Administração do PostgreSQL |

---

## Arquitetura

### Fluxo de Dados

```text
+----------------------+
|      Generator       |
| Dados bancários      |
| sintéticos           |
+----------+-----------+
           |
           | Geração e carga
           v
+----------------------+
|    PostgreSQL OLTP   |
| Dados transacionais  |
+----------+-----------+
           |
           | Extração
           v
+----------------------+
|        Bronze        |
| Dados brutos e       |
| históricos           |
| Formato Parquet      |
+----------+-----------+
           |
           | Validação e transformação
           v
+----------------------+
|        Silver        |
| Limpeza e validação  |
| Padronização         |
| Quarentena           |
+----------+-----------+
           |
           | Modelagem analítica
           v
+----------------------+
|     Gold / dbt       |
| Modelos analíticos   |
| Dimensões e fatos    |
+----------+-----------+
           |
           v
+----------------------+
|   Dados Analíticos   |
+----------+-----------+
           |
           +------------------+
           |                  |
           v                  v
+------------------+  +------------------+
|     Grafana      |  |     Metabase     |
| Dashboards       |  | Exploração e     |
| e indicadores    |  | visualizações    |
+------------------+  +------------------+

          Apache Airflow
     Orquestração das tarefas
```

O Apache Airflow atua como camada de orquestração, coordenando as tarefas conforme as DAGs. O dbt gerencia os modelos SQL e os testes da modelagem analítica.

### Responsabilidades das Camadas

- **Generator:** gera dados bancários sintéticos para simular operações financeiras.
- **PostgreSQL OLTP:** armazena os dados transacionais de origem.
- **Bronze:** mantém os dados extraídos em formato bruto, organizados por lote.
- **Silver:** principal fronteira de qualidade; aplica validações, limpeza, padronização e tratamento de inconsistências.
- **Gold:** disponibiliza conjuntos de dados estruturados e orientados à análise de negócio.
- **dbt:** gerencia transformações SQL, dependências entre modelos e testes de qualidade.
- **Apache Airflow:** orquestra as tarefas, gerencia dependências e permite acompanhar execuções e logs.
- **Grafana e Metabase:** exploração, visualização e dashboards.

---

## Estrutura do Projeto

```text
data-pipeline-repository/
│
├── airflow/
│   ├── dags/
│   │   └── banking_pipeline.py
│   ├── logs/
│   └── plugins/
│
├── configs/
│
├── database/
│   ├── ddl/
│   │   └── 01_create_tables.sql
│   └── seeds/
│       └── 01_seed_transaction_types.sql
│
├── dbt/
│   ├── models/
│   ├── tests/
│   └── profiles.yml
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── runbook.md
│   └── testing.md
│
├── src/
│   ├── bronze/
│   │   └── bronze.py
│   ├── extraction/
│   │   └── extract.py
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   ├── cards.py
│   │   ├── customers.py
│   │   ├── generate_data.py
│   │   ├── helpers.py
│   │   ├── loans.py
│   │   └── transactions.py
│   ├── gold/
│   │   └── gold.py
│   ├── silver/
│   │   ├── config.py
│   │   ├── io.py
│   │   ├── silver.py
│   │   ├── transformations.py
│   │   └── validation.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── config.py
│   └── main.py
│
├── tests/
│   ├── test_database.py
│   ├── test_generator.py
│   ├── test_silver_integration.py
│   ├── test_silver_quarantine.py
│   ├── test_silver_transformations.py
│   └── test_silver_validation.py
│
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
└── README.md
```

---

## Início Rápido

```bash
# 1. Variáveis de ambiente
cp .env.example .env

# 2. Infraestrutura
docker compose up -d

# 3. Dependências Python
uv sync

# 4. Pipeline completo (Generator → Bronze → Silver → Gold)
uv run python -m main --stage full

# 5. Modelos e testes dbt
dbt run  --project-dir dbt --profiles-dir dbt
dbt test --project-dir dbt --profiles-dir dbt

# 6. Validações do código
uv run ruff check .
uv run mypy src
uv run pytest
```

---

## Configuração de Ambiente

O projeto usa variáveis de ambiente para centralizar as configurações. Crie o `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Exemplo:

```env
APP_NAME=data-pipeline
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO
TIMEZONE=America/Sao_Paulo

POSTGRES_HOST=localhost
POSTGRES_PORT=15432
POSTGRES_DB=banking_oltp
POSTGRES_USER=banking_user
POSTGRES_PASSWORD=change_me

PGADMIN_EMAIL=admin@local.dev
PGADMIN_PASSWORD=change_me
PGADMIN_PORT=5050

FAKER_LOCALE=pt_BR
FAKER_SEED=42

NUM_AGENCIAS=10
NUM_CLIENTES=1000
NUM_CONTAS=1200
NUM_CARTOES=900
NUM_EMPRESTIMOS=400
NUM_TRANSACOES=10000
```

**Atenção:**

- Não versione o `.env`; somente o `.env.example`, sem credenciais reais.
- Dentro da rede Docker, o hostname do PostgreSQL é diferente do usado a partir da máquina local (`localhost:15432`). Configure as conexões do Airflow e do dbt de acordo com o ambiente em que rodam.
- As configurações da aplicação são carregadas e centralizadas em `src/config.py`.

### Ambiente Python

O projeto usa `uv` e requer `Python >= 3.11,<3.12`.

```bash
uv sync
uv run python --version
```

---

## Infraestrutura com Docker

O Docker Compose executa os serviços do ambiente local:

- PostgreSQL (OLTP)
- pgAdmin
- Apache Airflow e seus serviços auxiliares (banco de metadados, scheduler, DAG processor etc.)
- Grafana
- Metabase

```bash
docker compose up -d      # subir os serviços
docker compose ps         # verificar o estado
docker compose down       # parar, preservando os volumes
```

### Portas de Acesso

| Serviço | Endereço local | Finalidade |
|---|---|---|
| PostgreSQL | `localhost:15432` | Banco transacional |
| pgAdmin | http://localhost:5050 | Administração do banco |
| Grafana | http://localhost:3000 | Dashboards |
| Metabase | http://localhost:3001 | Exploração e visualização |
| Airflow | http://localhost:8080 | Orquestração do pipeline |

Confirme as portas no `docker-compose.yml`.

### Comandos Úteis

```bash
docker compose logs --tail=100 banking-postgres
docker compose logs --tail=100 banking-metabase
docker compose logs --tail=100 airflow-scheduler
docker compose logs --tail=100 airflow-dag-processor
docker compose restart banking-metabase
```

> **Cuidado:** `docker compose down -v` remove os volumes, apagando os dados locais do PostgreSQL e das demais ferramentas. Evite-o em diagnósticos comuns.

---

## Banco de Dados

O banco transacional é o PostgreSQL 17, com as tabelas:

```text
agencias
clientes
contas
cartoes
emprestimos
tipos_transacao
transacoes
```

### Principais Relacionamentos

```text
agencias
   |
   +---- contas
             |
             +---- clientes
             |
             +---- cartoes

clientes
   |
   +---- emprestimos

contas
   |
   +---- transacoes

tipos_transacao
   |
   +---- transacoes
```

Os relacionamentos representam a estrutura lógica do domínio; chaves e cardinalidades efetivas estão no DDL. A documentação completa está em `docs/data_dictionary.md`.

### Inicialização e Idempotência

Os scripts abaixo são montados no diretório de inicialização do PostgreSQL:

```text
database/ddl/01_create_tables.sql
database/seeds/01_seed_transaction_types.sql
```

- Eles são executados automaticamente **quando o volume do PostgreSQL é criado** (diretório de dados vazio). Alterações nos scripts **não** são reaplicadas em um volume já inicializado.
- O DDL usa `CREATE TABLE IF NOT EXISTS` e o seed trata conflitos, evitando recriação de objetos e inserções duplicadas.

---

## Generator

Gera dados bancários sintéticos com Faker para agências, clientes, contas, cartões, empréstimos e transações. A lógica é dividida em módulos (`accounts.py`, `cards.py`, `customers.py`, `loans.py`, `transactions.py`, `helpers.py` e `generate_data.py`).

```bash
uv run python -m main --stage generator
```

- Os dados são inseridos no PostgreSQL.
- Os IDs são incrementais e o sistema verifica CPFs e números de cartão existentes para evitar colisões.
- Idioma e semente são configuráveis (`FAKER_LOCALE=pt_BR`, `FAKER_SEED=42`).
- Valores monetários usam `Decimal` em Python e tipos numéricos no PostgreSQL, evitando erros de precisão do `float`.

---

## Ponto de Entrada do Pipeline

O ponto de entrada é `src/main.py`, com os estágios:

```text
generator
bronze
silver
gold
full
```

| Comando | Descrição |
|---|---|
| `uv run python -m main --stage generator` | Gera e carrega dados sintéticos no PostgreSQL |
| `uv run python -m main --stage bronze` | Extrai o PostgreSQL para a Bronze (Parquet) |
| `uv run python -m main --stage silver` | Valida e padroniza o último batch completo da Bronze |
| `uv run python -m main --stage gold` | Gera os datasets analíticos a partir da Silver |
| `uv run python -m main --stage full` | Executa Generator → Bronze → Silver → Gold |

Caso o módulo não seja encontrado a partir da raiz do repositório, consulte o `docs/runbook.md`.

---

## Camada Bronze

Extrai os dados do PostgreSQL e armazena uma cópia bruta e histórica em Parquet, adicionando metadados de ingestão. Tabelas extraídas: `agencias`, `clientes`, `contas`, `cartoes`, `emprestimos`, `tipos_transacao` e `transacoes`.

Os dados são organizados por data de ingestão e `batch_id` (único por execução), preservando o histórico:

```text
data/
└── bronze/
    └── clientes/
        └── ingestion_date=2026-09-18/
            └── batch_id=<UUID>/
                └── clientes.parquet
```

---

## Camada Silver

Responsável por qualidade, validação, transformação e padronização dos dados da Bronze. Módulos:

```text
src/silver/
├── config.py          # configuração
├── io.py              # leitura e escrita de arquivos
├── silver.py          # orquestração da etapa
├── transformations.py # transformações
└── validation.py      # validações
```

### Validações e Padronizações

- Colunas obrigatórias, chaves primárias, duplicidades e valores nulos.
- Integridade de chaves estrangeiras.
- Normalização de CPF, cartões, valores monetários, datas e timestamps.
- Validação de regras específicas das transações.

Somente registros que passam pelas regras são disponibilizados na Silver.

### Quarentena de Dados

Registros inválidos **não são descartados**: vão para uma área de quarentena, com o motivo da rejeição, para investigação posterior.

```text
data/
└── silver_rejects/
    └── <table>/
        └── ingestion_date=YYYY-MM-DD/
            └── batch_id=<UUID>/
                └── rejected.parquet
```

### Particionamento e Reprocessamento

A Silver é particionada por `ingestion_date` e `batch_id`. Cada execução cria um novo batch e **os anteriores são preservados**; o último batch completo é identificado pelo marcador de sucesso da Silver.

```text
data/
└── silver/
    └── clientes/
        ├── ingestion_date=2026-09-16/
        │   └── batch_id=AAAA/
        │       └── clientes.parquet
        └── ingestion_date=2026-09-18/
            └── batch_id=BBBB/
                └── clientes.parquet
```

---

## Camada Gold

A Gold consome **somente dados validados da Silver**, a partir do último batch completo, e produz conjuntos orientados à análise de negócio. Ela pode ser produzida por dois caminhos complementares: os datasets gerados em Python (`src/gold/gold.py`) e os modelos dbt (próxima seção).

### Datasets Analíticos (Python)

| Dataset | Conteúdo |
|---|---|
| Volume diário de transações | Data, quantidade de transações e volume financeiro total |
| Volume diário de transações PIX | Data, quantidade de transações PIX e volume financeiro |
| Volume financeiro por agência | Agência, quantidade de transações e volume total |
| Transações por cliente | Cliente e quantidade de transações |
| Saldo médio por agência | Agência, quantidade de contas e saldo médio |
| Clientes com empréstimos | Cliente, quantidade de empréstimos, valor total contratado e média de parcelas |
| Volume de empréstimos | Quantidade total, volume total contratado e média de parcelas |

```bash
uv run python -m main --stage gold
```

---

## Modelagem Analítica com dbt

O dbt organiza as transformações SQL, as dependências entre modelos e os testes de qualidade.

**Modelos de staging:**

```text
stg_agencias
stg_cartoes
stg_clientes
stg_contas
stg_emprestimos
stg_tipos_transacao
stg_transacoes
```

**Modelos dimensionais e factuais:**

| Modelo | Descrição |
|---|---|
| `dim_cliente` | Dimensão de clientes |
| `dim_conta` | Dimensão de contas |
| `dim_tipo_transacao` | Dimensão dos tipos de transação |
| `dim_data` | Dimensão de calendário |
| `fato_emprestimo` | Fato para análises de empréstimos (volume, valores contratados, parcelas) |

```bash
dbt run  --project-dir dbt --profiles-dir dbt
dbt test --project-dir dbt --profiles-dir dbt
```

A execução depende de um `profiles.yml` válido, das credenciais configuradas e da disponibilidade do banco de destino. Campos e regras de cada modelo estão nos arquivos SQL e YAML do projeto.

---

## Orquestração com Apache Airflow

O Airflow coordena as tarefas por meio de DAGs (*Directed Acyclic Graphs*). A DAG principal é a `banking_pipeline`, definida em `airflow/dags/banking_pipeline.py`.

- **Agendamento:** diário, pela expressão cron `0 6 * * *`. O horário efetivo depende do fuso horário configurado no Airflow.
- **Escopo:** etapas de processamento dos dados e execução dos modelos dbt, conforme as tarefas configuradas na DAG.
- **Recursos:** dependências entre tarefas, tentativas adicionais após falhas (quando configuradas), logs e estados das tarefas, e conexões com serviços como o PostgreSQL.

Acesso: http://localhost:8080

```bash
docker compose logs --tail=100 airflow-scheduler
docker compose logs --tail=100 airflow-dag-processor
```

Para validar uma execução, consulte a DAG na interface e verifique o estado e os logs de cada tarefa.

---

## Visualização e Exploração de Dados

### Grafana

Dashboards e indicadores sobre transações e empréstimos, conforme os painéis configurados. Acesso: http://localhost:3000

### Metabase

Exploração dos dados, perguntas, gráficos e dashboards de negócio, conectado ao PostgreSQL e aos modelos analíticos. Acesso: http://localhost:3001

Em caso de `Failed to fetch` no login, verifique o serviço antes de redefinir credenciais, pois o erro não indica necessariamente senha incorreta:

```bash
docker compose ps
docker compose logs --tail=100 banking-metabase
docker compose restart banking-metabase
```

### pgAdmin

Administração do PostgreSQL, consultas e inspeção de estruturas. Acesso: http://localhost:5050

---

## Testes e Qualidade de Código

### Testes Automatizados

Os testes cobrem banco de dados, Generator, validações, transformações, integração e quarentena da Silver:

```text
tests/
├── test_database.py
├── test_generator.py
├── test_silver_integration.py
├── test_silver_quarantine.py
├── test_silver_transformations.py
└── test_silver_validation.py
```

```bash
uv run pytest
uv run pytest tests/test_silver_quarantine.py -v   # somente quarentena
```

Os testes de quarentena verificam a criação do arquivo de rejeitados, a presença e o motivo da rejeição, a permanência dos registros válidos na Silver e a separação entre válidos e inválidos.

### Lint e Tipos

```bash
uv run ruff check .
uv run mypy src
```

### Testes dbt

```bash
dbt test --project-dir dbt --profiles-dir dbt
```

### Validação Completa antes do Commit

```bash
uv run ruff check .
uv run mypy src
uv run pytest
dbt test --project-dir dbt --profiles-dir dbt
```

Na última validação registrada, os resultados foram: Ruff `All checks passed!`, MyPy `Success: no issues found in 23 source files` e Pytest `43 passed`. Esses números mudam conforme o projeto evolui; atualize-os somente após verificá-los na versão atual.

---

## Logs e Tratamento de Erros

- O projeto usa o `logging` padrão do Python, configurado em `src/main.py` e controlado por `LOG_LEVEL`.
- Os logs informam etapa atual, conexão com o banco, status, batch selecionado, quantidade de registros e erros.
- Exceções inesperadas são registradas com detalhes e propagadas ao ponto de entrada; `main.py` retorna código diferente de zero quando uma etapa falha, evitando falhas silenciosas.
- Utilitários compartilhados ficam em `src/utils/`; a conexão com o PostgreSQL está centralizada em `src/utils/database.py`.

---

## Armazenamento e Reprodutibilidade

Os dados gerados ficam em `data/` e são ignorados pelo Git:

```text
data/
├── bronze/
├── silver/
├── silver_rejects/
└── gold/
```

- A mesma `FAKER_SEED` permite reproduzir a geração dos dados sintéticos.
- Cada execução recebe um `batch_id` único, combinando geração reproduzível com histórico de execuções.

---

## Segurança e Dados Sensíveis

- Campos como CPF, número de cartão e nome de cliente são **gerados sinteticamente** e não representam pessoas ou informações financeiras reais.
- O projeto não deve ser alimentado com dados pessoais reais sem autorização e controles apropriados.
- Não versione senhas, tokens ou chaves; mantenha o `.env` protegido pelo `.gitignore`.
- Configure as conexões do Airflow de acordo com a rede e o ambiente de execução.
- Evite remover volumes persistentes sem compreender as consequências.

---

## Documentação Complementar

| Arquivo | Conteúdo |
|---|---|
| `docs/architecture.md` | Arquitetura, fluxo de dados e responsabilidades das camadas |
| `docs/data_dictionary.md` | Entidades, atributos, relacionamentos e regras de qualidade |
| `docs/runbook.md` | Execução, validação e troubleshooting |
| `docs/testing.md` | Estratégia de testes e procedimentos de validação |

---

## Princípios de Projeto

- **Separação de responsabilidades:** cada camada e módulo tem um papel específico.
- **Preservação dos dados brutos:** a Bronze mantém o histórico extraído.
- **Qualidade antes da análise:** a Silver valida e padroniza antes do consumo pela Gold.
- **Processamento histórico:** batches permitem reprocessar sem sobrescrever execuções anteriores.
- **Inicialização idempotente:** scripts de banco podem ser aplicados sem duplicar objetos ou dados.
- **Configuração centralizada:** variáveis de ambiente carregadas em um único ponto.
- **Testabilidade:** módulos pequenos, testáveis individualmente.
- **Observabilidade:** logs e interface do Airflow dão visibilidade da execução.
- **Dados sintéticos:** desenvolvimento, testes e demonstração sem informações pessoais reais.

---

## Status do Projeto

A implementação atual reúne:

- Banco PostgreSQL OLTP com inicialização automática, DDL idempotente e seed dos tipos de transação
- Infraestrutura Dockerizada (PostgreSQL, pgAdmin, Airflow, Grafana e Metabase)
- Generator modularizado de dados sintéticos
- Camada Bronze com Parquet particionado por data de ingestão e batch
- Camada Silver com validação, transformação, quarentena, particionamento e preservação histórica de batches
- Camada Gold com datasets analíticos em Python
- Modelagem analítica com dbt (staging, dimensões e fato de empréstimos)
- Orquestração com Apache Airflow (DAG `banking_pipeline`, agendamento diário)
- Dashboards e exploração com Grafana e Metabase
- Configuração centralizada, logging e tratamento de exceções
- Ponto de entrada único com execução por etapa e completa
- Testes automatizados e validação com Ruff e MyPy

O projeto oferece um ambiente local completo de Engenharia de Dados para geração, processamento, validação, modelagem, orquestração e análise de dados bancários sintéticos.