# Projeto de Engenharia de Dados — Banking Data Pipeline

Pipeline de dados end-to-end para simulação, ingestão, tratamento e análise de transações bancárias.

O projeto simula o ciclo de vida dos dados de uma instituição financeira, desde a geração de dados sintéticos em Python até sua disponibilização em camadas analíticas para consumo por ferramentas de Business Intelligence.

A origem dos dados é um banco de dados transacional (OLTP), alimentado por dados fictícios gerados utilizando a biblioteca Python Faker.

## Arquitetura

```text
Python + Faker
      │
      │ Dados sintéticos
      ▼
PostgreSQL — OLTP
      │
      │ Extração
      ▼
   Bronze
      │
      │ Limpeza e padronização
      ▼
   Silver
      │
      │ Modelagem e agregação
      ▼
    Gold
      │
      ▼
Power BI / Metabase
```

### Modelo Medallion

O pipeline utiliza uma arquitetura Medallion dividida em três camadas:

* **Bronze:** armazenamento dos dados extraídos da origem em formato bruto, preservando o histórico.
* **Silver:** dados limpos, tratados, deduplicados e padronizados.
* **Gold:** dados modelados e agregados para responder às perguntas de negócio.

A arquitetura segue a proposta apresentada no projeto, na qual a Bronze mantém uma cópia fiel da origem, a Silver realiza os tratamentos de qualidade e a Gold prepara os dados para consumo analítico.

## Stack

| Camada                 | Tecnologia              |
| ---------------------- | ----------------------- |
| Linguagem              | Python 3.11+            |
| Geração de dados       | Faker                   |
| Banco OLTP             | PostgreSQL              |
| Administração do banco | pgAdmin                 |
| Containerização        | Docker / Docker Compose |
| Driver PostgreSQL      | psycopg                 |
| Dados intermediários   | Parquet                 |
| Transformações         | Python / SQL            |
| BI                     | Power BI / Metabase     |
| Controle de versão     | Git / GitHub            |

## Modelo OLTP

O banco transacional simula as principais operações de um banco digital.

### Entidades

```text
Agencias
    │
    └── Contas
            │
            ├── Cartoes
            │
            └── Transacoes

Clientes
    │
    ├── Contas
    └── Emprestimos

Tipos_Transacao
    │
    └── Transacoes
```

Principais tabelas:

* `Agencias`
* `Clientes`
* `Contas`
* `Cartoes`
* `Emprestimos`
* `Tipos_Transacao`
* `Transacoes`

As tabelas possuem chaves primárias e estrangeiras para garantir a integridade dos relacionamentos do modelo transacional.

## Dados

Os dados são sintéticos e gerados utilizando a biblioteca Faker.

O gerador cria registros fictícios para simular um ambiente bancário realista, incluindo:

* Clientes
* Agências
* Contas
* Cartões
* Empréstimos
* Tipos de transação
* Transações bancárias

Nenhum dado bancário real é utilizado no projeto.

## Setup

### 1. Clonar o repositório

```bash
git clone <REPOSITORY_URL>
cd data-pipeline-repository
```

### 2. Configurar as variáveis de ambiente

```bash
cp .env.example .env
```

Preencha o `.env` com as configurações locais do PostgreSQL e do ambiente.

> O arquivo `.env` não deve ser versionado.

### 3. Subir o ambiente com Docker

```bash
docker compose up -d
```

O Docker será responsável por executar os serviços necessários para o ambiente local.

### 4. Verificar os containers

```bash
docker compose ps
```

### 5. Criar a estrutura do banco

A estrutura do PostgreSQL será criada utilizando os scripts SQL presentes em:

```text
database/ddl/
```

## PostgreSQL e pgAdmin

### PostgreSQL

Por padrão:

```text
Host: localhost
Port: 5432
Database: banking_oltp
```

### pgAdmin

O pgAdmin será utilizado como interface de administração e consulta do PostgreSQL.

Por padrão:

```text
http://localhost:5050
```

Ao conectar o pgAdmin ao PostgreSQL dentro da rede Docker, o host do banco deve utilizar o nome do serviço definido no `docker-compose.yml`, e não necessariamente `localhost`.

## Executar o gerador de dados

Depois que o banco estiver criado:

```bash
python src/generator/generate_data.py
```

O gerador será responsável por criar e inserir os dados sintéticos no banco OLTP.

A geração deve respeitar a ordem das dependências:

```text
Agencias
    ↓
Clientes
    ↓
Contas
    ↓
Cartoes
    ↓
Emprestimos
    ↓
Tipos_Transacao
    ↓
Transacoes
```

Essa ordem evita a criação de registros com referências inexistentes.

## Pipeline

O pipeline é dividido em etapas independentes.

### Extração

```text
PostgreSQL OLTP
      │
      ▼
src/extraction/
      │
      ▼
Dados brutos
```

A etapa de extração lê os dados do banco transacional e disponibiliza os registros para processamento.

### Bronze

```text
Origem
  ↓
Bronze
```

A Bronze preserva os dados em seu formato original, mantendo o histórico da extração.

Os dados poderão ser armazenados em formato Parquet:

```text
data/
└── bronze/
    ├── agencias/
    ├── clientes/
    ├── contas/
    ├── cartoes/
    ├── emprestimos/
    ├── tipos_transacao/
    └── transacoes/
```

### Silver

A Silver é responsável pela qualidade e padronização dos dados.

Tratamentos previstos:

* Remoção de registros duplicados
* Tratamento de valores nulos
* Padronização de CPF
* Padronização de datas e horários
* Validação de relacionamentos
* Validação de valores monetários

Esses tratamentos estão alinhados às regras descritas no projeto.

### Gold

A Gold contém dados preparados para análise e consumo por ferramentas de BI.

Exemplos de indicadores:

* Total de movimentações via PIX por dia
* Volume financeiro movimentado por agência
* Quantidade de transações por cliente
* Saldo médio por agência
* Clientes com empréstimos
* Volume total de empréstimos
* Indicadores de inadimplência

O projeto prevê a utilização da camada Gold para responder perguntas de negócio por meio de dados agregados.


## Segurança

Informações sensíveis não devem ser armazenadas diretamente no código-fonte.

As configurações locais serão mantidas em:

```text
.env
```

O arquivo será ignorado pelo Git.

Um modelo sem credenciais reais será disponibilizado em:

```text
.env.example
```

## Estrutura do projeto

```text
data-pipeline-repository/
│
├── docker/
│
├── database/
│   ├── ddl/
│   │   └── 01_create_tables.sql
│   │
│   └── seeds/
│       └── 01_seed_transaction_types.sql
│
├── src/
│   ├── generator/
│   │   └── generate_data.py
│   │
│   ├── extraction/
│   │   └── extract.py
│   │
│   ├── bronze/
│   │   └── bronze.py
│   │
│   ├── silver/
│   │   └── silver.py
│   │
│   └── gold/
│       └── gold.py
│
├── tests/
│   ├── test_database.py
│   └── test_generator.py
│
├── configs/
│
├── docs/
│   ├── architecture.md
│   └── data_dictionary.md
│
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Próximos passos

O primeiro objetivo técnico é estabelecer uma base OLTP consistente em PostgreSQL, executar o ambiente por Docker e validar completamente o modelo antes da geração dos dados sintéticos.

A partir dessa base, o projeto evoluirá para as camadas Bronze, Silver e Gold e posteriormente para o consumo analítico.
