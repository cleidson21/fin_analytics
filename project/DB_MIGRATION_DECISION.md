# DB Migration Decision (Gate 0.1)

## ETAPA 1 — LEITURA E REGISTRO DA INFRAESTRUTURA DE BANCO

**Evidências Físicas da Camada de Banco de Dados:**
- **Script Bootstrap:** `database/create_db.py` lido. O comentário principal declara explicitamente: *Executes all migrations in order to build the SQLite database from scratch. Replaces any prior SQLAlchemy ORM setup. The database IS the source of truth.*
- **Migrations Existentes:** 13 arquivos físicos.
- **Padrão de Nomenclatura:** `<numero>_<descricao>.sql` (ex: `001_core_identity.sql`, `013_position_snapshots.sql`).
- **Fluxo Utilizado Atualmente:** Scripts SQL puros sendo aplicados sequencialmente em vez de depender de migrações geradas pelo ORM em Python.
- **Alembic:** O arquivo `alembic.ini` **NÃO EXISTE**. O diretório `alembic/env.py` **NÃO EXISTE**. O versionamento por Alembic é rigorosamente inexistente neste projeto.

---

## ETAPA 2 — AUDITORIA DE DIVERGÊNCIA

**1. Qual é o mecanismo oficial de versionamento do banco?**
R: Scripts Raw SQL (`.sql`) numerados sequencialmente e orquestrados customizadamente pelo `create_db.py`.

**2. Existe Alembic implementado? / Existe coexistência?**
R: Não existe Alembic implementado e, portanto, não há coexistência. O V3 abdicou 100% de ORM para versionamento em favor do SQL puro estrutural.

**3. O Plano da Sprint 3C.2 está consistente com a infraestrutura encontrada?**
R: **NÃO.** O plano anterior exigia executar `alembic revision` e `alembic upgrade`.

**4. Onde a divergência ocorre e por que?**
A divergência ocorreu porque o plano padronizado presumiu uma stack típica de Python+SQLAlchemy+Alembic, sem varrer fisicamente a customização de design do FinAnalytics V3, onde o banco é a "single source of truth" e as migrations são textuais para garantir a compatibilidade universal via SQLite.

**5. Qual impacto teria se ignorada?**
Desastre arquitetural. Instalar e rodar o Alembic do zero criaria um ecossistema órfão concorrendo com o `create_db.py`, além de forçar a criação de metadata (`alembic_version`) que não foi planejada. Isso destruiria o fluxo limpo de migrations que o projeto já construiu da versão 001 à 013.

---

## ETAPA 3 — DECISÃO ARQUITETURAL

**Diagnóstico:** Arquitetura do V3 proíbe ferramentas intrusivas como Alembic na geração do banco, focando em raw SQL transparente e legível.

**Comparação Técnica para este Cenário (Alembic × SQL Puro):**
- *Alembic:* Adiciona dependência, gera acoplamento ORM-Schema, cria tabelas de versionamento ocultas, mas automatiza a sintaxe.
- *SQL Puro (Atual):* Simplicidade máxima, documentação explícita do DDL sem depender de engines secundárias, zero acoplamento ORM.

**Recomendação Arquitetural Oficial:**
- **ABORTAR ALEMBIC IMEDIATAMENTE.**
- **Adotar Padrão Nativo:** Criar o arquivo `database/migrations/014_cei_trades.sql`.
- **Evolução Segura:** Manter o SQLAlchemy no `backend/` unicamente para consultar (Repository) ou inserir dados (Upsert via Core), mas nunca para moldar a tabela (`metadata.create_all`). O model no backend servirá apenas como abstração, enquanto a Tabela será regida unicamente pelo arquivo `014`.
