# ADR 010: Sistema Single User com Bootstrap Automático

**Data:** 2026-07-19
**Status:** Aceito

## Contexto
O FIN Analytics V1 foi inicialmente concebido com um fluxo tradicional de cadastro (Signup, `CreateUserUseCase`, verificação de e-mail), sugerindo um sistema multiusuário. No entanto, o propósito central do projeto é ser uma ferramenta analítica pessoal para um único utilizador e administrador do sistema.

## Problema
Manter uma infraestrutura e arquitetura multiusuário para um software pessoal adiciona complexidade desnecessária. Isso implica gerenciar fluxos de recuperação de senha, bloqueio de contas repetidas, e-mails de confirmação e um endpoint público de cadastro que poderia ser explorado.

## Decisão
O FIN Analytics V1 será oficialmente um sistema **Single User**.
1. **Bootstrap Automático:** Se não houver nenhum usuário no banco na primeira execução, o sistema criará automaticamente um usuário padrão (admin).
2. **Usuário Admin:** O único usuário do sistema será sempre criado com a role `ADMIN`.
3. **Sem Cadastro:** Não existirá fluxo, endpoint, ou Use Case de criação de usuários (`CreateUserUseCase`). Todo o processo de onboarding aberto foi descartado.
4. **Sem CRUD de Usuários:** Não será possível adicionar usuários via interface.
5. A autenticação continua via JWT de forma padrão, apenas garantindo acesso a esse usuário pré-existente.

## Consequências
- **Simplificação:** A camada de segurança fica substancialmente mais enxuta, focando apenas na autenticação (login/refresh).
- **Remoção de Código:** `CreateUserUseCase`, `CreateUserCommand`, evento `UserCreated`, e dependências para disparos de e-mail de boas-vindas foram removidos da especificação.
- A arquitetura (com `user_id` vinculado às transações e portfólios) permanece compatível com expansão futura. Se decidirmos reverter para Multi User no futuro, basta criarmos uma nova ADR, reinserirmos os Use Cases de cadastro e o domínio não será quebrado.

## Alternativas Consideradas
- **Multi User completo (Rejeitado):** Traz carga desnecessária para a versão inicial do projeto.
- **Cadastro Privado (Rejeitado):** Permitir convites (invites). Complexo e não resolve a demanda imediata de um único usuário dono.
