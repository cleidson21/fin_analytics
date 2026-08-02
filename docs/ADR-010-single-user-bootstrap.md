# ADR-010: Single-User Bootstrap

## Contexto

A aplicação tem como modelo primário a utilização `Single-User`, ou seja, projetada para um único usuário final. Entretanto, o sistema requer um usuário inicial para gerenciar permissões e rotinas básicas.

## Decisão

Foi decidido implementar uma rotina idempotente de `BootstrapAdmin` que garantirá a existência de um usuário `admin` no banco de dados.

## Implementação (BootstrapAdmin)

- Executado automaticamente durante o `Lifespan` da aplicação.
- Identificador de busca (e-mail): `admin`
- Senha inicial: `admin` (armazenada com hash padrão bcrypt)
- Role: `ADMIN`
- O processo é idempotente: caso o usuário já exista (por e-mail `admin`), a rotina não realizará nenhuma alteração e simplesmente continuará o fluxo.
