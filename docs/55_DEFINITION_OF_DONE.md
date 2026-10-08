> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Definition of Done — FIN Analytics

Uma **Vertical Slice** está **CONCLUÍDA** somente quando TODOS os itens abaixo estiverem marcados **E** o usuário tiver validado manualmente.

---

## Status de uma Vertical Slice

| Status | Critério |
|---|---|
| 🔲 **Não Iniciado** | Nenhum arquivo criado |
| 🔄 **Em Andamento** | Implementação parcial em progresso |
| 🧪 **EM VALIDAÇÃO PELO USUÁRIO** | Implementação concluída, aguardando validação humana |
| ✅ **Concluída** | Todos os critérios do DoD atendidos + aprovação explícita do usuário |
| ⚫ **Bloqueada** | Aguardando conclusão de fase anterior |

> [!CAUTION]
> **É PROIBIDO** marcar uma Vertical Slice como ✅ Concluída enquanto:
> - Existir qualquer mock, placeholder ou `console.log` simulado para o objetivo principal da slice
> - O usuário não tiver executado o fluxo manualmente no frontend-dev
> - O usuário não tiver aprovado explicitamente

---

## Checklist de Validação de Vertical Slice

### 1. Documentação
- [ ] `docs/` atualizado para refletir o que foi implementado
- [ ] Nenhum documento em `docs/` contraditório com a implementação
- [ ] Se decisão arquitetural nova: ADR criado em `docs/decisions/`
- [ ] Use Case correspondente em `37_USE_CASES.md` marcado como implementado
- [ ] Endpoint correspondente em `20_REST_ENDPOINTS.md` marcado como implementado

### 2. Domain
- [ ] Entidade canônica definida em `domain/entities/`
- [ ] Value Objects usados corretamente
- [ ] Enums usados (sem strings mágicas)
- [ ] Regras de negócio documentadas em `33_DOMAIN_RULES.md`

### 3. Application
- [ ] Use Case implementado seguindo `37_USE_CASES.md`
- [ ] Command ou Query tipado(a) com validação
- [ ] DTO(s) de Request e Response definidos em `40_DTOS.md`
- [ ] Port(s) utilizado(s) — sem import de Infrastructure
- [ ] Evento(s) publicado(s) após commit (se aplicável)

### 4. Infrastructure
- [ ] ORM Model criado em `infrastructure/persistence/models/`
- [ ] Migration Alembic revisada e aplicada explicitamente; runtime/lifespan não executa DDL
- [ ] Repository concreto implementando o Port correspondente
- [ ] Repository converte ORM Model → Domain Entity antes de retornar

### 5. API
- [ ] Router implementado em `api/routers/`
- [ ] Request validado via Pydantic
- [ ] Response serializado via DTO de Response (nunca ORM Model)
- [ ] Autenticação/autorização verificada (se endpoint protegido)
- [ ] Erros mapeados para códigos HTTP corretos
- [ ] Documentação OpenAPI gerada corretamente no Swagger

### 6. Segurança
- [ ] Nenhum secret exposto em log
- [ ] Nenhum secret hardcoded no código
- [ ] Dados sensíveis não retornados em DTOs de Response

### 7. Backend Funcional
- [ ] `uvicorn backend.main:app --reload` inicia sem erros
- [ ] Swagger abre em `http://localhost:8000/docs`
- [ ] Endpoint responde corretamente via Swagger ou curl
- [ ] Banco de dados grava e persiste os dados

### 8. frontend-dev Funcional
- [ ] `npm run dev` inicia sem erros em `http://localhost:5173`
- [ ] Interface consome a API real (zero mocks, zero placeholders)
- [ ] Fluxo de sucesso funciona corretamente na tela
- [ ] Fluxo de erro exibe o JSON real da API (sem `alert()`, sem mensagem genérica)

### 9. Validação Manual pelo Usuário
- [ ] Usuário executou o fluxo manualmente no frontend-dev
- [ ] Usuário confirmou que o comportamento é o esperado
- [ ] Usuário aprovou explicitamente a Vertical Slice
- [ ] Status atualizado para ✅ Concluída no `54_IMPLEMENTATION_ORDER.md`

---

## O que deve ser entregue ao final de cada Vertical Slice

O agente deve gerar obrigatoriamente:

### Como executar
Passo a passo completo para subir o ambiente.

### Como testar
Passo a passo exato do fluxo a ser validado no frontend-dev.

### Resultado esperado
Descrição exata do comportamento esperado em caso de sucesso.

### Casos negativos
Quais erros o usuário deve tentar provocar e qual resposta esperar.

### Checklist de validação para o usuário
Lista de verificação para o usuário preencher.

---

## Regra sobre Mocks

> [!CAUTION]
> **É PROIBIDO** considerar uma Sprint concluída quando existir qualquer funcionalidade simulada (mock, placeholder, `console.log` ou dados hardcoded) para o **objetivo principal** daquela Sprint.
>
> Exemplos proibidos:
> - `setJsonResponse('Iniciando login... (simulado)')`
> - `return {"status": "fake_ok"}`
> - `// TODO: implementar`
> - Dados hardcoded retornados diretamente pelo router sem Use Case

---

## Exemplo de DoD Aplicado

```
Vertical Slice: Autenticação (Fase 1)

Documentação
- [x] 20_REST_ENDPOINTS.md: POST /auth/login marcado como ✅
- [x] 37_USE_CASES.md: UC-01 marcado como ✅ IMPLEMENTADO
- [x] Nenhuma contradição documental

Domain
- [x] User entity com campos corretos

Application
- [x] AuthenticateUserUseCase implementado
- [x] AuthenticateUserCommand tipado
- [x] AuthTokenDTO e UserResponseDTO definidos
- [x] IUserRepository, IPasswordHasher, IJWTService usados via Port

Infrastructure
- [x] UserModel + tabela criada via Lifespan
- [x] SQLAlchemyUserRepository
- [x] BCryptPasswordHasher
- [x] JWTService

API
- [x] POST /auth/login implementado
- [x] 401 para credenciais inválidas
- [x] Swagger documentado

Backend
- [x] Uvicorn inicia sem erros
- [x] Swagger em http://localhost:8000/docs

frontend-dev
- [x] Formulário de login sem mock
- [x] AuthTokenDTO exibido em caso de sucesso
- [x] JSON de erro exibido em caso de falha

Validação pelo usuário
- [x] Usuário executou login com admin/admin
- [x] Usuário viu Access Token na tela
- [x] Usuário aprovou

Status: ✅ CONCLUÍDA
```

---

## Critérios Específicos Adicionais por VS

### VS-04: Assinaturas e Parcelamentos
- [ ] Migration de `purchase_id` gerada e aplicada com sucesso sem corromper transações antigas.
- [ ] Testes Unitários de Matemática Inferencial (motor retroativo de parcelas) validados com mínimo de 90% de cobertura no Use Case.
- [ ] DTOs expondo exatamente as chaves snake_case esperadas pelo Frontend (atenção ao alias `total_installments`).
- [ ] Nenhum erro 422 na API ao omitir o `month` (validação Pydantic opcional tratada corretamente).
- [ ] A tela Frontend Oficial do projeto exibe os dados consumidos sem skeletons e sem interações simuladas (Mocks).
