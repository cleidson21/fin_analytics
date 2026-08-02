> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Implantação — FIN Analytics

---

## Stack de Implantação

| Ambiente | Backend | Frontend | Banco | Proxy |
|---|---|---|---|---|
| Development | `uvicorn --reload` | `npm run dev` | SQLite (arquivo) | — |
| Production (futuro) | `gunicorn + uvicorn` | build estático | SQLite ou PostgreSQL | nginx |

---

## Docker (Desenvolvimento)

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./database:/app/database
      - ./backend:/app/backend
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

## Inicialização (Sequência Obrigatória)

```
1. Copiar .env.example → .env e preencher variáveis
2. pip install -r requirements.txt
3. alembic upgrade head          # criar/atualizar schema do banco
4. python scripts/seed.py        # popular categorias padrão (se existir)
5. uvicorn backend.main:app --reload
```

---

## Migrations em Produção

```
# NUNCA rodar alembic upgrade head em produção sem backup
1. pg_dump / sqlite3 .backup (backup primeiro)
2. alembic upgrade head
3. Verificar saúde: GET /api/v1/health
```

---

## Health Check

```
GET /api/v1/health

Response 200:
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "database": "ok",
  "timestamp": "2024-07-19T20:00:00Z"
}

Response 503 (banco indisponível):
{
  "status": "degraded",
  "database": "error",
  "message": "Database connection failed"
}
```

---

## Backup e Restore (SQLite)

```bash
# Backup
python scripts/backup.py
# Cria: backups/fin_analytics_YYYYMMDD_HHMM.db

# Restore
python scripts/restore.py --file backups/fin_analytics_20240719_2000.db
```

**Frequência recomendada:** Diário (antes de qualquer migration).

---

## Migração Futura: SQLite → PostgreSQL

Quando migrar (volume > 1GB ou múltiplos usuários simultâneos):

1. Atualizar `DATABASE_URL` para `postgresql+asyncpg://...`
2. Instalar `asyncpg`: `pip install asyncpg`
3. Exportar dados do SQLite: `python scripts/export_sqlite.py`
4. Criar banco PostgreSQL e rodar `alembic upgrade head`
5. Importar dados: `python scripts/import_postgres.py`
6. Verificar integridade: `python scripts/verify_migration.py`

> [!NOTE]
> O ORM SQLAlchemy abstrai as diferenças entre SQLite e PostgreSQL. A troca é apenas na `DATABASE_URL` e no driver.
