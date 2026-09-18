# Data Pipeline Repository

Pipeline de Engenharia de Dados de ponta a ponta para um domínio bancário, desenvolvido com Python, PostgreSQL, Docker, Pandas e PyArrow.

O projeto simula um ambiente de dados bancários, gera dados sintéticos, armazena esses dados em um banco PostgreSQL, realiza a extração para a camada Bronze, valida e padroniza os dados na camada Silver e produz conjuntos de dados analíticos na camada Gold.

---

## Visão Geral

O projeto implementa um pipeline de dados utilizando uma arquitetura em camadas:

```text
PostgreSQL OLTP
      |
      v
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
      |
      v
Dados Analíticos
```

Cada camada possui uma responsabilidade específica:

- **PostgreSQL** — banco de dados transacional de origem.
- **Generator** — geração de dados bancários sintéticos.
- **Bronze** — armazenamento dos dados extraídos em formato bruto e histórico.
- **Silver** — validação, limpeza e padronização dos dados.
- **Gold** — geração de conjuntos de dados orientados à análise de negócio.

O pipeline pode ser executado por etapa individualmente ou de ponta a ponta através de um único ponto de entrada.

---

# Arquitetura

## Fluxo de Dados

```text
+----------------------+
|      PostgreSQL      |
|        OLTP          |
+----------+-----------+
           |
           | Extração
           v
+----------------------+
|      Generator       |
|  Dados bancários     |
|      sintéticos      |
+----------+-----------+
           |
           v
+----------------------+
|       Bronze         |
| Dados brutos e       |
|      históricos      |
|      Parquet         |
+----------+-----------+
           |
           | Validação
           v
+----------------------+
|       Silver         |
| Limpeza + validação  |
| Padronização         |
| Particionamento      |
+----------+-----------+
           |
           | Análise
           v
+----------------------+
|        Gold          |
| Dados orientados     |
|      ao negócio      |
+----------------------+
```

A camada Silver funciona como a principal fronteira de qualidade dos dados.

Somente dados validados e padronizados na Silver são utilizados pela camada Gold.

---

# Tecnologias

O projeto utiliza:

- Python 3.11
- PostgreSQL 17
- Docker
- Docker Compose
- Pandas
- PyArrow
- Faker
- Psycopg2
- Python Dotenv
- Pytest
- Ruff
- MyPy
- uv

---

# Estrutura do Projeto

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
│   │
│   ├── bronze/
│   │   └── bronze.py
│   │
│   ├── extraction/
│   │   └── extract.py
│   │
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   ├── cards.py
│   │   ├── customers.py
│   │   ├── generate_data.py
│   │   ├── helpers.py
│   │   ├── loans.py
│   │   └── transactions.py
│   │
│   ├── gold/
│   │   └── gold.py
│   │
│   ├── silver/
│   │   ├── config.py
│   │   ├── io.py
│   │   ├── silver.py
│   │   ├── transformations.py
│   │   └── validation.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── database.py
│   │
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

# Banco de Dados

O banco de dados transacional utilizado pelo projeto é o PostgreSQL 17.

O banco possui as seguintes tabelas:

```text
agencias
clientes
contas
cartoes
emprestimos
tipos_transacao
transacoes
```

## Principais relacionamentos

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

A documentação completa das tabelas, campos e relacionamentos está disponível em:

```text
docs/data_dictionary.md
```

---

# Docker

A infraestrutura do banco de dados é executada utilizando Docker Compose.

O projeto possui dois serviços principais:

```text
banking-postgres
banking-pgadmin
```

O banco utiliza:

```text
PostgreSQL 17
```

O pgAdmin é disponibilizado como ferramenta para administração do banco.

---

# Inicialização do Banco

O banco é inicializado automaticamente quando um novo volume PostgreSQL é criado.

Os seguintes scripts são montados no diretório de inicialização do PostgreSQL:

```text
database/ddl/01_create_tables.sql
database/seeds/01_seed_transaction_types.sql
```

Dessa forma, não é necessário executar manualmente o DDL antes de utilizar o projeto.

O seed dos tipos de transação também é executado automaticamente.

---

# DDL Idempotente

Os scripts de criação do banco utilizam operações idempotentes.

Por exemplo:

```sql
CREATE TABLE IF NOT EXISTS ...
```

O seed dos tipos de transação também utiliza tratamento de conflito para evitar inserções duplicadas.

Isso permite inicializar o banco sem tentar recriar objetos que já existem.

---

# Subindo a Infraestrutura

Certifique-se de que o Docker Desktop esteja em execução.

Suba os serviços:

```bash
docker compose up -d
```

Verifique os containers:

```bash
docker compose ps
```

Os serviços esperados são:

```text
banking-postgres
banking-pgadmin
```

O PostgreSQL deve estar saudável antes da execução do pipeline.

---

# pgAdmin

O pgAdmin está disponível em:

```text
http://localhost:5050
```

A porta é configurada através de:

```env
PGADMIN_PORT=5050
```

As credenciais utilizadas pelo pgAdmin são definidas no arquivo `.env`.

Para o ambiente local, o PostgreSQL utiliza a porta configurada em:

```env
POSTGRES_PORT=15432
```

---

# Configuração de Ambiente

O projeto utiliza variáveis de ambiente para centralizar as configurações.

Crie um arquivo `.env` baseado no `.env.example`.

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

O arquivo `.env` não deve ser enviado para o Git.

Somente o `.env.example` deve ser versionado.

---

# Ambiente Python

O projeto utiliza o `uv` para gerenciamento do ambiente Python e das dependências.

Instale as dependências:

```bash
uv sync
```

Verifique a versão do Python:

```bash
uv run python --version
```

O projeto requer:

```text
Python >= 3.11,<3.12
```

---

# Generator

O Generator é responsável pela geração de dados bancários sintéticos utilizando a biblioteca Faker.

São gerados dados para:

- Agências
- Clientes
- Contas
- Cartões
- Empréstimos
- Transações

O Generator foi dividido em vários módulos para evitar a concentração de toda a lógica em um único arquivo.

```text
src/generator/
├── accounts.py
├── cards.py
├── customers.py
├── generate_data.py
├── helpers.py
├── loans.py
└── transactions.py
```

Cada módulo possui uma responsabilidade específica.

---

# Dados Sintéticos

O projeto utiliza Faker para gerar os dados.

A localidade utilizada é:

```env
FAKER_LOCALE=pt_BR
```

A semente de geração é configurada através de:

```env
FAKER_SEED=42
```

Os dados gerados são destinados exclusivamente a:

- Desenvolvimento
- Testes
- Demonstração

Nenhum dado real de cliente deve ser utilizado no projeto.

---

# PII e Dados Sensíveis

O projeto possui campos que representam informações potencialmente sensíveis, como:

- CPF
- Número de cartão
- Nome de cliente

Esses dados são gerados de forma sintética.

Eles não representam pessoas reais nem informações financeiras reais.

O projeto não deve ser alimentado com dados pessoais reais.

---

# Valores Monetários

Os valores financeiros são tratados utilizando tipos baseados em decimal.

O Generator utiliza:

```python
Decimal
```

em vez de `float` para valores monetários.

Isso evita problemas comuns de precisão causados pela representação binária de números de ponto flutuante.

No PostgreSQL, os campos financeiros utilizam tipos numéricos apropriados para valores monetários.

---

# Ponto de Entrada do Pipeline

O projeto possui um ponto de entrada centralizado:

```text
src/main.py
```

Ele permite executar as etapas individualmente ou executar todo o pipeline.

As etapas disponíveis são:

```text
generator
bronze
silver
gold
full
```

---

# Executando o Generator

Para executar somente o Generator:

```bash
uv run python -m main --stage generator
```

O Generator insere os dados sintéticos no PostgreSQL.

Os IDs são gerados de forma incremental e o sistema verifica CPFs e números de cartão existentes para evitar colisões.

---

# Camada Bronze

A camada Bronze realiza a extração dos dados do PostgreSQL e armazena uma cópia bruta e histórica em formato Parquet.

As tabelas extraídas são:

```text
agencias
clientes
contas
cartoes
emprestimos
tipos_transacao
transacoes
```

A Bronze preserva os dados extraídos e adiciona informações relacionadas à ingestão.

---

# Particionamento da Bronze

Os dados da Bronze são organizados por data de ingestão e identificador do batch.

Exemplo:

```text
data/
└── bronze/
    └── clientes/
        └── ingestion_date=2026-09-18/
            └── batch_id=<UUID>/
                └── clientes.parquet
```

Cada execução do processo recebe um `batch_id` único.

Isso permite manter diferentes execuções do pipeline no histórico.

---

# Executando a Bronze

Para executar a camada Bronze:

```bash
uv run python -m main --stage bronze
```

A etapa realiza a extração do PostgreSQL e grava os dados em arquivos Parquet.

---

# Camada Silver

A camada Silver é responsável pela qualidade, validação, transformação e padronização dos dados provenientes da Bronze.

Ela foi dividida em módulos:

```text
src/silver/
├── config.py
├── io.py
├── silver.py
├── transformations.py
└── validation.py
```

Essa divisão separa responsabilidades como:

- Configuração
- Leitura e escrita de arquivos
- Orquestração do pipeline
- Transformações
- Validações

---

# Qualidade dos Dados na Silver

A camada Silver realiza validações como:

- Colunas obrigatórias
- Chaves primárias
- Duplicidades
- Valores nulos
- Integridade de chaves estrangeiras
- Normalização de CPF
- Normalização de cartões
- Normalização de valores monetários
- Normalização de datas
- Normalização de timestamps
- Validação de transações

Somente os registros que passam pelas regras de validação são disponibilizados na Silver.

---

# Quarentena de Dados

Registros inválidos não são simplesmente descartados.

Eles são enviados para uma área de quarentena.

A estrutura é:

```text
data/
└── silver_rejects/
    └── <table>/
        └── ingestion_date=YYYY-MM-DD/
            └── batch_id=<UUID>/
                └── rejected.parquet
```

Os registros rejeitados recebem informações adicionais sobre o motivo da rejeição.

Isso permite investigar posteriormente os problemas encontrados nos dados.

---

# Particionamento da Silver

A Silver é particionada por:

```text
ingestion_date
batch_id
```

Exemplo:

```text
data/
└── silver/
    └── clientes/
        ├── ingestion_date=2026-09-16/
        │   └── batch_id=AAAA/
        │       └── clientes.parquet
        │
        └── ingestion_date=2026-09-18/
            └── batch_id=BBBB/
                └── clientes.parquet
```

Cada execução cria um novo batch.

Os batches anteriores são preservados.

---

# Reprocessamento da Silver

O reprocessamento da Silver não sobrescreve os batches anteriores.

Exemplo:

```text
Primeira execução
      |
      v
   Batch A
      |
      v
    Silver


Segunda execução
      |
      v
   Batch B
      |
      v
    Silver


Terceira execução
      |
      v
   Batch C
      |
      v
    Silver
```

Os batches anteriores permanecem armazenados.

A aplicação identifica o último batch completo através do marcador de sucesso da Silver.

Isso permite realizar reprocessamentos sem perder o histórico existente.

---

# Executando a Silver

Para executar a camada Silver:

```bash
uv run python -m main --stage silver
```

A etapa identifica automaticamente o último batch completo da Bronze e realiza o processamento.

---

# Camada Gold

A camada Gold produz conjuntos de dados orientados para análise de negócio.

A Gold consome somente dados validados da Silver.

Antes de gerar os datasets analíticos, o pipeline identifica o último batch completo da Silver.

Os datasets analíticos atuais incluem:

- Volume diário de transações
- Volume diário de transações PIX
- Volume financeiro por agência
- Transações por cliente
- Saldo médio por agência
- Clientes com empréstimos
- Volume de empréstimos

---

# Datasets Analíticos da Gold

## Volume Diário de Transações

Apresenta:

- Data da transação
- Quantidade de transações
- Volume financeiro total

---

## Volume Diário de Transações PIX

Apresenta:

- Data da transação
- Quantidade de transações PIX
- Volume financeiro de transações PIX

---

## Volume Financeiro por Agência

Apresenta:

- Agência
- Quantidade de transações
- Volume financeiro total

---

## Transações por Cliente

Apresenta:

- Cliente
- Quantidade de transações

---

## Saldo Médio por Agência

Apresenta:

- Agência
- Quantidade de contas
- Saldo médio

---

## Clientes com Empréstimos

Apresenta métricas relacionadas aos empréstimos dos clientes:

- Cliente
- Quantidade de empréstimos
- Valor total contratado
- Média de parcelas

---

## Volume de Empréstimos

Apresenta métricas agregadas de empréstimos:

- Quantidade total de empréstimos
- Volume total contratado
- Média de parcelas

---

# Executando a Gold

Para executar a camada Gold:

```bash
uv run python -m main --stage gold
```

A Gold lê o último batch completo da Silver e gera os datasets analíticos.

---

# Executando o Pipeline Completo

O pipeline completo pode ser executado através de um único comando:

```bash
uv run python -m main --stage full
```

A ordem de execução é:

```text
1. Generator
       |
       v
2. Bronze
       |
       v
3. Silver
       |
       v
4. Gold
```

Isso permite reproduzir todo o fluxo de dados desde a geração dos dados sintéticos até a criação dos datasets analíticos.

---

# Configuração Centralizada

As configurações principais do projeto estão centralizadas em:

```text
src/config.py
```

O módulo carrega as variáveis de ambiente e disponibiliza as configurações utilizadas pelo pipeline.

Isso evita duplicação de configurações de banco e aplicação em diferentes arquivos.

---

# Utilitários

As funcionalidades compartilhadas ficam em:

```text
src/utils/
```

Atualmente, a lógica de conexão com PostgreSQL está centralizada em:

```text
src/utils/database.py
```

Isso evita que diferentes partes do pipeline tenham implementações duplicadas da conexão com o banco.

---

# Logs

O projeto utiliza o sistema padrão de logging do Python.

A configuração dos logs é centralizada através de:

```text
src/main.py
```

O nível de log pode ser configurado através de:

```env
LOG_LEVEL=INFO
```

Os logs apresentam informações como:

- Etapa atual do pipeline
- Conexão com o banco
- Status do processamento
- Batch selecionado
- Quantidade de registros
- Erros e exceções

---

# Tratamento de Erros

As etapas do pipeline possuem tratamento explícito de exceções.

Erros inesperados são registrados nos logs com informações da exceção e propagados para o ponto de entrada principal.

O `main.py` retorna um código diferente de zero quando uma etapa do pipeline falha.

Isso evita que falhas críticas sejam ignoradas silenciosamente.

---

# Testes

O projeto possui testes automatizados para diferentes partes do pipeline.

Os testes cobrem:

```text
Banco de dados
Generator
Validações da Silver
Transformações da Silver
Integração da Silver
Quarentena da Silver
```

Os arquivos de teste são:

```text
tests/
├── test_database.py
├── test_generator.py
├── test_silver_integration.py
├── test_silver_quarantine.py
├── test_silver_transformations.py
└── test_silver_validation.py
```

---

# Executando os Testes

Para executar toda a suíte de testes:

```bash
uv run pytest
```

A validação atual do projeto apresenta:

```text
43 passed
```

---

# Testes de Quarentena

O projeto possui testes específicos para verificar o comportamento da quarentena.

Os testes verificam, entre outros pontos:

- Criação do arquivo de registros rejeitados
- Presença das informações de rejeição
- Registro do motivo da rejeição
- Permanência dos registros válidos na Silver
- Separação entre registros válidos e inválidos

Para executar somente os testes de quarentena:

```bash
uv run pytest tests/test_silver_quarantine.py -v
```

---

# Qualidade do Código

O projeto utiliza Ruff para análise estática e linting.

Execute:

```bash
uv run ruff check .
```

Resultado esperado:

```text
All checks passed!
```

---

# Verificação de Tipos

O projeto utiliza MyPy para verificação estática de tipos.

Execute:

```bash
uv run mypy src
```

A validação atual apresenta:

```text
Success: no issues found in 23 source files
```

---

# Validação Completa

Antes de realizar um commit, execute:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

Resultados esperados:

```text
Ruff
All checks passed!

MyPy
Success: no issues found in 23 source files

Pytest
43 passed
```

---

# Comandos Úteis do Docker

Subir a infraestrutura:

```bash
docker compose up -d
```

Verificar os containers:

```bash
docker compose ps
```

Ver logs do PostgreSQL:

```bash
docker compose logs postgres
```

Ver logs do pgAdmin:

```bash
docker compose logs pgadmin
```

Parar a infraestrutura:

```bash
docker compose down
```

Parar a infraestrutura e remover o volume do PostgreSQL:

```bash
docker compose down -v
```

O parâmetro `-v` remove o volume do banco e, consequentemente, os dados locais do PostgreSQL.

---

# Comandos Úteis do Pipeline

Executar o Generator:

```bash
uv run python -m main --stage generator
```

Executar a Bronze:

```bash
uv run python -m main --stage bronze
```

Executar a Silver:

```bash
uv run python -m main --stage silver
```

Executar a Gold:

```bash
uv run python -m main --stage gold
```

Executar o pipeline completo:

```bash
uv run python -m main --stage full
```

---

# Reprodutibilidade

A geração de dados sintéticos utiliza uma semente configurável do Faker:

```env
FAKER_SEED=42
```

A utilização da mesma semente permite reproduzir o comportamento da geração dos dados sintéticos.

Cada execução do pipeline também recebe um `batch_id` único.

Dessa forma, o projeto combina geração de dados reproduzível com controle histórico das execuções.

---

# Armazenamento dos Dados

Os dados gerados pelo pipeline são armazenados no diretório:

```text
data/
```

As principais camadas são:

```text
data/
├── bronze/
├── silver/
├── silver_rejects/
└── gold/
```

Os arquivos gerados pelo pipeline são ignorados pelo Git através do `.gitignore`.

Isso evita que arquivos Parquet e outros dados gerados localmente sejam enviados para o repositório.

---

# Documentação

A documentação técnica adicional está disponível no diretório:

```text
docs/
```

## Arquitetura

```text
docs/architecture.md
```

Contém a descrição detalhada da arquitetura, fluxo de dados e responsabilidades das camadas.

## Dicionário de Dados

```text
docs/data_dictionary.md
```

Contém as entidades, atributos, relacionamentos e regras de qualidade dos dados.

## Runbook

```text
docs/runbook.md
```

Contém instruções operacionais para execução, validação e troubleshooting do pipeline.

## Testes

```text
docs/testing.md
```

Contém a estratégia de testes e os procedimentos de validação do projeto.

---

# Princípios de Projeto

O projeto segue os seguintes princípios:

## Separação de Responsabilidades

Cada camada e módulo possui uma responsabilidade específica.

## Preservação dos Dados Brutos

A Bronze mantém os dados extraídos de forma histórica.

## Qualidade Antes da Análise

A Silver valida e padroniza os dados antes que eles sejam consumidos pela Gold.

## Processamento Histórico

A utilização de batches permite que novos processamentos sejam realizados sem sobrescrever os batches anteriores.

## Inicialização Idempotente

Os scripts de inicialização do banco utilizam operações idempotentes.

## Configuração Centralizada

As configurações são carregadas a partir de variáveis de ambiente e centralizadas no projeto.

## Testabilidade

As responsabilidades foram divididas em módulos que podem ser testados individualmente.

## Observabilidade

Os logs fornecem visibilidade sobre a execução do pipeline e seus possíveis erros.

## Dados Sintéticos

O projeto utiliza dados sintéticos para desenvolvimento, testes e demonstração, evitando a utilização de informações pessoais reais.

---

# Exemplo de Execução Completa

Uma execução local completa pode ser realizada seguindo os passos abaixo.

### 1. Subir a infraestrutura

```bash
docker compose up -d
```

### 2. Instalar as dependências

```bash
uv sync
```

### 3. Executar o pipeline completo

```bash
uv run python -m main --stage full
```

### 4. Executar as validações

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

Resultados esperados:

```text
Ruff
All checks passed!

MyPy
Success: no issues found in 23 source files

Pytest
43 passed
```

---

# Fluxo Final do Pipeline

A arquitetura final pode ser resumida da seguinte forma:

```text
                         +------------------+
                         |    PostgreSQL    |
                         |      OLTP        |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |    Generator     |
                         | Dados sintéticos |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |      Bronze      |
                         | Dados brutos      |
                         | Dados históricos  |
                         |     Parquet      |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |      Silver      |
                         |    Validação     |
                         |  Transformação    |
                         |    Quarentena     |
                         |  Particionamento  |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         |       Gold       |
                         |    Analytics     |
                         | Dados de negócio |
                         +------------------+
```

---

# Status do Projeto

A implementação atual possui:

- Banco PostgreSQL OLTP
- Infraestrutura Dockerizada
- Inicialização automática do banco
- DDL idempotente
- Seed dos tipos de transação
- Gerador de dados sintéticos
- Generator modularizado
- Configuração centralizada
- Utilitários compartilhados
- Conexão centralizada com PostgreSQL
- Logging
- Tratamento de exceções
- Camada Bronze
- Validação da Silver
- Transformações da Silver
- Quarentena de dados inválidos
- Particionamento da Silver
- Preservação histórica dos batches
- Camada Gold
- Datasets analíticos
- Ponto de entrada centralizado
- Execução por etapa
- Execução completa do pipeline
- Testes automatizados
- Validação com Ruff
- Validação com MyPy
- Processamento Parquet com PyArrow

O projeto fornece um ambiente local completo de Engenharia de Dados para geração, processamento, validação e análise de dados bancários sintéticos.