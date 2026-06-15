# BACKEND V2 BASELINE

**Inventário do Estado Atual (Antes do Refactoring da Camada de Domínio)**

A atual estrutura `app/` no Backend legou uma divisão horizontal onde rotas, serviços e modelos se misturam ou referenciam uns aos outros sem respeitar isolamentos de domínio.

## 1. Estrutura Atual
* **`app/api/routes`:** Contém controladores amarrados (ex: `accounts.py`, `investments.py`, `dashboard.py`) que realizam chamadas extensas e complexas.
* **`app/api/services`:** O local onde se encontram "God Classes", como `WealthAnalyticsService`, que processa rentabilidade cruzada acessando múltiplas tabelas indiretamente.
* **`app/models` / `app/api/schemas`:** Muitas vezes o banco retorna tuplas cruas do SQLite ou pydantic schemas, sem ORM bem delimitado (o MVP anterior rodou sem SQLAlchemy ou com ele apenas parcial).

## 2. Dependências Atuais
* O sistema V1 depende de SQL Raw espalhado em Repositories e Services.
* Não existe um `SessionFactory` limpo usando SQLAlchemy moderno, a dependência global `deps.get_db` apenas instaura conexões sqlite3 ou psycopg2 manuais em certas fases.

## 3. Acoplamentos Atuais
* **Frontend Acoplado:** As rotas formatam respostas (ex: JSON do Recharts) no meio da lógica de negócios, acoplando a camada de visualização à camada de serviço.
* **ETL vs Domínio:** A lógica de *Parsing* e importação está acoplada à rota da web (`POST /import`), travando o ciclo HTTP.

## 4. Problemas Atuais
* Ausência de limites de Domínio (DDD).
* Difícil testabilidade (Unit Tests não podem mockar facilmente o banco porque o SQL está inserido nos Services).
* Código repetitivo.
