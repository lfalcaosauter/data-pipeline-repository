-- ============================================================
-- BANKING DATA MART - BUSINESS QUERIES
-- ============================================================


-- ============================================================
-- 01. MOVIMENTAÇÃO FINANCEIRA TOTAL
-- ============================================================

SELECT
    SUM(valor) AS valor_total_movimentado
FROM dbt_dev.fato_transacao;


-- ============================================================
-- 02. QUANTIDADE TOTAL DE OPERAÇÕES
-- ============================================================

SELECT
    COUNT(*) AS quantidade_operacoes
FROM dbt_dev.fato_transacao;


-- ============================================================
-- 03. MOVIMENTAÇÃO POR TIPO DE TRANSAÇÃO
-- ============================================================

-- 3. Movimentação por tipo de transação
SELECT
    dtt.tipo_transacao_id,
    dtt.descricao AS tipo_transacao,
    COUNT(*) AS quantidade_operacoes,
    SUM(ft.valor) AS valor_total_movimentado
FROM dbt_dev.fato_transacao ft
INNER JOIN dbt_dev.dim_tipo_transacao dtt
    ON ft.tipo_transacao_sk = dtt.tipo_transacao_sk
GROUP BY
    dtt.tipo_transacao_id,
    dtt.descricao
ORDER BY
    valor_total_movimentado DESC;

-- ============================================================
-- 04. EVOLUÇÃO MENSAL DAS TRANSAÇÕES
-- ============================================================

SELECT
    dd.ano,
    dd.mes,
    dd.nome_mes,
    COUNT(*) AS quantidade_operacoes,
    SUM(ft.valor) AS valor_total_movimentado
FROM dbt_dev.fato_transacao ft

INNER JOIN dbt_dev.dim_data dd
    ON ft.data_sk = dd.data_sk

GROUP BY
    dd.ano,
    dd.mes,
    dd.nome_mes

ORDER BY
    dd.ano,
    dd.mes;


-- ============================================================
-- 05. EMPRÉSTIMOS - VISÃO GERAL
-- ============================================================

SELECT
    COUNT(*) AS quantidade_emprestimos,
    SUM(valor_contratado) AS valor_total_contratado,
    AVG(valor_contratado) AS valor_medio_contratado,
    AVG(parcelas) AS media_parcelas
FROM dbt_dev.fato_emprestimo;


-- ============================================================
-- 06. EMPRÉSTIMOS POR ANO
-- ============================================================

SELECT
    dd.ano,
    COUNT(*) AS quantidade_emprestimos,
    SUM(fe.valor_contratado) AS valor_total_contratado,
    AVG(fe.valor_contratado) AS valor_medio_contratado
FROM dbt_dev.fato_emprestimo fe

INNER JOIN dbt_dev.dim_data dd
    ON fe.data_sk = dd.data_sk

GROUP BY
    dd.ano

ORDER BY
    dd.ano;


-- ============================================================
-- 07. EMPRÉSTIMOS POR QUANTIDADE DE PARCELAS
-- ============================================================

SELECT
    parcelas,
    COUNT(*) AS quantidade_emprestimos,
    SUM(valor_contratado) AS valor_total_contratado,
    AVG(valor_contratado) AS valor_medio_contratado
FROM dbt_dev.fato_emprestimo

GROUP BY
    parcelas

ORDER BY
    parcelas;


-- ============================================================
-- 08. TOP 10 CLIENTES POR VALOR DE EMPRÉSTIMOS
-- ============================================================

SELECT
    dc.cliente_id,
    COUNT(fe.emprestimo_id) AS quantidade_emprestimos,
    SUM(fe.valor_contratado) AS valor_total_contratado
FROM dbt_dev.fato_emprestimo fe

INNER JOIN dbt_dev.dim_cliente dc
    ON fe.cliente_sk = dc.cliente_sk

GROUP BY
    dc.cliente_id

ORDER BY
    valor_total_contratado DESC

LIMIT 10;


-- ============================================================
-- 09. EMPRÉSTIMOS POR MÊS
-- ============================================================

SELECT
    dd.ano,
    dd.mes,
    dd.nome_mes,
    COUNT(*) AS quantidade_emprestimos,
    SUM(fe.valor_contratado) AS valor_total_contratado
FROM dbt_dev.fato_emprestimo fe

INNER JOIN dbt_dev.dim_data dd
    ON fe.data_sk = dd.data_sk

GROUP BY
    dd.ano,
    dd.mes,
    dd.nome_mes

ORDER BY
    dd.ano,
    dd.mes;


-- ============================================================
-- 10. VALOR MÉDIO DA PARCELA CONTRATADA
-- ============================================================

SELECT
    AVG(valor_medio_parcela) AS valor_medio_parcela
FROM dbt_dev.fato_emprestimo;