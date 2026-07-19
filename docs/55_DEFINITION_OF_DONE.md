> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Definition of Done — FIN Analytics

Uma funcionalidade está **CONCLUÍDA** somente quando TODOS os itens abaixo estiverem marcados.

---

## Checklist Obrigatório

### Documentação
- [ ] `docs/` atualizado se alguma decisão mudou
- [ ] Nenhum documento em `docs/` está contraditório com a implementação
- [ ] Se decisão arquitetural nova: ADR criado em `docs/decisions/`

### Domain
- [ ] Entidade canônica definida em `domain/entities/`
- [ ] Value Objects usados corretamente
- [ ] Enums usados (sem strings mágicas)
- [ ] Regras de negócio documentadas em `33_DOMAIN_RULES.md`

### Application
- [ ] Use Case implementado seguindo `37_USE_CASES.md`
- [ ] Command ou Query tipado com validação
- [ ] DTO(s) de Request e Response definidos em `40_DTOS.md`
- [ ] Port(s) utilizado(s) (sem import de Infrastructure)
- [ ] Evento(s) publicado(s) após commit (se aplicável)

### Infrastructure
- [ ] ORM Model criado em `infrastructure/persistence/models/`
- [ ] Migration Alembic gerada e aplicada
- [ ] Repository concreto implementando o Port correspondente
- [ ] Repository converte ORM Model → Domain Entity antes de retornar
- [ ] Unit of Work gerencia o commit/rollback

### API
- [ ] Router implementado em `api/routers/`
- [ ] Request validado via Pydantic (DTO de Request)
- [ ] Response serializado via DTO de Response (nunca ORM Model)
- [ ] Autenticação/autorização verificada (se endpoint protegido)
- [ ] Erros mapeados para códigos de `45_ERROR_HANDLING.md`
- [ ] Documentação OpenAPI gerada corretamente (docstring + type hints)

### Segurança
- [ ] Nenhum secret exposto em log
- [ ] Nenhum secret hardcoded no código
- [ ] Dados sensíveis não retornados em DTOs de Response

### Logging
- [ ] `INFO` no início e fim do Use Case
- [ ] `ERROR` com contexto suficiente para depuração
- [ ] `request_id` e `correlation_id` propagados

### Testes
- [ ] Testes unitários do Use Case (ports mockados) — cobertura ≥ 90%
- [ ] Testes unitários do Mapper — cobertura 100%
- [ ] Testes de integração do Repository (banco in-memory)
- [ ] Testes de API (httpx AsyncClient)
- [ ] Todos os testes passando em `pytest`
- [ ] Cobertura não regrediu

### Qualidade
- [ ] Sem imports circulares
- [ ] Sem SQL raw fora de Repositories
- [ ] Sem `datetime.now()` fora de `IClock`
- [ ] Sem `os.environ` fora de `core/config.py`
- [ ] Type hints completos em todas as funções públicas
- [ ] Docstrings nos métodos públicos do Use Case e Mapper

---

## Estados Possíveis de uma Funcionalidade

| Estado | Critério |
|---|---|
| 🔴 **Não Iniciado** | Nenhum arquivo criado |
| 🟡 **Em Progresso** | Implementação parcial |
| 🟠 **Sem Testes** | Implementado mas sem cobertura completa |
| 🟢 **Concluído** | Todos os itens do DoD marcados |
| ⚫ **Bloqueado** | Aguardando dependência |

---

## Exemplo de Uso do DoD

```
Funcionalidade: AuthenticateUser (UC-01)

- [x] docs/ atualizado (nenhuma mudança necessária)
- [x] Domain: User entity com campos corretos
- [x] Application: AuthenticateUserUseCase implementado
- [x] Application: AuthenticateUserCommand com validação
- [x] Application: AuthTokenDTO definido
- [x] Application: IUserRepository, ISecrets, IClock usados via Port
- [x] Application: nenhum import de Infrastructure
- [x] Infrastructure: UserModel + migration
- [x] Infrastructure: SQLAlchemyUserRepository
- [x] API: POST /auth/login implementado
- [x] API: 401 para credenciais inválidas
- [x] Segurança: senha nunca logada
- [x] Logging: INFO no início/fim, ERROR em falhas
- [x] Testes: UC mockado, Repository + banco, API endpoint
- [x] Qualidade: sem violações

Status: 🟢 CONCLUÍDO
```
