-- ============================================================
-- Banking Data Pipeline
-- Database Schema
-- ============================================================
--
-- PostgreSQL OLTP schema for the banking transaction pipeline.
-- The schema follows the project specification using
-- PostgreSQL-friendly snake_case naming conventions.
--
-- ============================================================


-- ============================================================
-- TABLE: agencias
-- ============================================================

CREATE TABLE IF NOT EXISTS agencias (
    agencia_id INT PRIMARY KEY,
    nome_agencia VARCHAR(50) NOT NULL,
    cidade VARCHAR(50) NOT NULL
);


-- ============================================================
-- TABLE: clientes
-- ============================================================

CREATE TABLE IF NOT EXISTS clientes (
    cliente_id INT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL
);


-- ============================================================
-- TABLE: tipos_transacao
-- ============================================================

CREATE TABLE IF NOT EXISTS tipos_transacao (
    tipo_transacao_id INT PRIMARY KEY,
    descricao VARCHAR(50) NOT NULL
);


-- ============================================================
-- TABLE: contas
-- ============================================================

CREATE TABLE IF NOT EXISTS contas (
    conta_id INT PRIMARY KEY,
    cliente_id INT NOT NULL,
    agencia_id INT NOT NULL,
    saldo NUMERIC(15, 2) NOT NULL,

    CONSTRAINT fk_contas_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes (cliente_id),

    CONSTRAINT fk_contas_agencia
        FOREIGN KEY (agencia_id)
        REFERENCES agencias (agencia_id)
);


-- ============================================================
-- TABLE: cartoes
-- ============================================================

CREATE TABLE IF NOT EXISTS cartoes (
    cartao_id INT PRIMARY KEY,
    conta_id INT NOT NULL,
    numero_cartao VARCHAR(16) NOT NULL UNIQUE,
    tipo_cartao VARCHAR(20) NOT NULL,

    CONSTRAINT fk_cartoes_conta
        FOREIGN KEY (conta_id)
        REFERENCES contas (conta_id)
);


-- ============================================================
-- TABLE: emprestimos
-- ============================================================

CREATE TABLE IF NOT EXISTS emprestimos (
    emprestimo_id INT PRIMARY KEY,
    cliente_id INT NOT NULL,
    valor_contratado NUMERIC(15, 2) NOT NULL,
    parcelas INT NOT NULL,
    data_contrato DATE NOT NULL,

    CONSTRAINT fk_emprestimos_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES clientes (cliente_id),

    CONSTRAINT chk_emprestimos_parcelas
        CHECK (parcelas > 0)
);


-- ============================================================
-- TABLE: transacoes
-- ============================================================

CREATE TABLE IF NOT EXISTS transacoes (
    transacao_id INT PRIMARY KEY,
    conta_origem_id INT NOT NULL,
    conta_destino_id INT NOT NULL,
    tipo_transacao_id INT NOT NULL,
    valor NUMERIC(15, 2) NOT NULL,
    data_hora TIMESTAMP NOT NULL,

    CONSTRAINT fk_transacoes_conta_origem
        FOREIGN KEY (conta_origem_id)
        REFERENCES contas (conta_id),

    CONSTRAINT fk_transacoes_conta_destino
        FOREIGN KEY (conta_destino_id)
        REFERENCES contas (conta_id),

    CONSTRAINT fk_transacoes_tipo
        FOREIGN KEY (tipo_transacao_id)
        REFERENCES tipos_transacao (tipo_transacao_id),

    CONSTRAINT chk_transacoes_contas_diferentes
        CHECK (conta_origem_id <> conta_destino_id)
);