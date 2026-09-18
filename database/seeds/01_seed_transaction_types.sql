INSERT INTO tipos_transacao (
    tipo_transacao_id,
    descricao
)
VALUES
    (1, 'PIX'),
    (2, 'TED'),
    (3, 'DOC'),
    (4, 'SAQUE'),
    (5, 'DEPOSITO')
ON CONFLICT (tipo_transacao_id) DO NOTHING;

