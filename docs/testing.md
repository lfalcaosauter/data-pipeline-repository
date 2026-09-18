# Estratégia de Testes — Banking Data Pipeline

## 1. Objetivo

Este documento descreve a estratégia de testes utilizada no Banking Data Pipeline.

Os testes têm como objetivo garantir:

- correção funcional;
- qualidade dos dados;
- integridade dos dados;
- comportamento esperado das transformações;
- funcionamento da quarantine;
- integridade dos batches;
- funcionamento das integrações entre as camadas;
- execução correta do pipeline end-to-end;
- qualidade estática do código.

---

## 2. Ferramentas

O projeto utiliza:

- Pytest para testes automatizados;
- Ruff para análise estática e lint;
- MyPy para verificação de tipos.

Comandos principais:

```bash
uv run pytest
uv run ruff check src
uv run mypy src