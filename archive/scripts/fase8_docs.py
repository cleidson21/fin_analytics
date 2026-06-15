import os

docs = {
    'financial_repository.md': '\n\n**Transaction Safety (FASE 8):** Operações de escrita agora são protegidas por explícitos blocos `BEGIN/COMMIT/ROLLBACK` orquestrados pelo `app.core.observability`.',
    'governance_repository.md': '\n\n**Transaction Safety (FASE 8):** A promoção de Staging e Rollbacks de Import operam com segurança atômica (`BEGIN TRANSACTION`) sob observabilidade de performance.',
    'financial_service.md': '\n\n**Observability (FASE 8):** Logs estruturados (`request_id`, `endpoint`, `duration_ms`) ofuscando dados sensíveis operam de forma subjacente.',
    'governance_service.md': '\n\n**Observability (FASE 8):** Registros de rollback e promoções de staging são injetados em um `MetricsRegistry` thread-safe.',
    'import_service.md': '\n\n**Production Hardening (FASE 8):** Testes end-to-end de fumaça garantem que as pipelines de inserção operam sob < 5% de overhead com as novas proteções transacionais.'
}

for name, content in docs.items():
    path = f'docs/architecture/{name}'
    if os.path.exists(path):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
