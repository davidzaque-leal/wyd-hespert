# Wyd Fansite (FastAPI)

Este repositório contém uma pequena aplicação FastAPI que consulta rankings remotos, persiste-os em banco de dados e serve páginas com os dados.

**Visão geral**
- A aplicação consulta APIs remotas (level e arena), persiste os dados no banco e serve templates Jinja2.
- Há um updater em background que sincroniza os dados a cada 1 hora.

**Requisitos**
- Python 3.10+
- pip

**Instalação**
1. Crie e ative um ambiente virtual (recomendado):

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

> Observação: o projeto usa SQLite por padrão (`./app.db`). Se preferir usar Postgres, instale um driver adicional (ex.: `psycopg2-binary`) e defina a variável `DATABASE_URL` (exemplo abaixo).

**Variáveis de ambiente**
- `DATABASE_URL` (opcional): URL de conexão SQLAlchemy.
  - Exemplo (SQLite - padrão): `sqlite:///./app.db`
  - Exemplo (Postgres): `postgresql+psycopg2://user:password@host:5432/dbname`

Se `DATABASE_URL` não for informado, a aplicação criará `./app.db` automaticamente e usará SQLite.

**Criar/Atualizar o banco**
- As tabelas são criadas automaticamente na inicialização da aplicação (ver [app/main.py](app/main.py)).
- Para reiniciar o banco com SQLite, pare a aplicação e remova `app.db` antes de iniciar.
- Se usar Postgres em produção, configure Alembic para migrações.

**Executando a aplicação**

```bash
uvicorn app.main:app --reload
```

- A aplicação ficará disponível em `http://127.0.0.1:8000/`.
- A primeira sincronização é executada no startup (pode demorar alguns segundos dependendo da API remota).
- Para checar status e última atualização: `GET /health`.

**Rotas principais**
- `/` — Home (index)
- `/ranking` — Ranking de Level
- `/arena/{category}` — Arena; `category` = `champion` ou `aspirant`
- `/ranking-combined` — Ranking combinado (Level + Arena)
- `/health` — Health check com `last_update`

**Arquivos importantes**
- [app/main.py](app/main.py) — inicialização, criação de tabelas e scheduler (intervalo padrão: 1 hora).
- [app/services/data_store.py](app/services/data_store.py) — camada que fornece dados para as views (carrega do DB e mantém backup JSON).
- [app/services/sync_service.py](app/services/sync_service.py) — lógica de sincronização e persistência no DB.
- [app/database.py](app/database.py) — engine e `SessionLocal`.
- [app/models.py](app/models.py) — modelos SQLAlchemy.
- [app/repositories](app/repositories) — repositórios para persistir/consultar dados.

**Intervalo de atualização**
- O updater em background chama `data_store.update_data()` a cada 3600 segundos (1 hora).
- Para alterar o intervalo, edite [app/main.py](app/main.py) no `background_updater()`.

**Logs e depuração**
- A aplicação imprime logs simples de sincronização no console.
- Para mais detalhes de SQL, ajuste `echo=True` em [app/database.py](app/database.py) (apenas para desenvolvimento).

**Usando Postgres em produção**
1. Instale driver:

```bash
pip install psycopg2-binary
```

2. Exporte `DATABASE_URL` antes de iniciar (exemplo Windows PowerShell):

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
uvicorn app.main:app --reload
```

3. Configure Alembic para migrações (opcional) — o projeto inclui `alembic` no `requirements.txt`.

**Problemas conhecidos e dicas**
- Se a API remota não responder, a aplicação mantém os dados do backup JSON (`data_backup.json`) e não perde o site.
- Caso precise forçar uma sincronização manual, reinicie a aplicação ou chame `SyncService.sync_all()` a partir de um shell Python apontando para o projeto.


Se quiser, eu posso:
- adicionar um endpoint protegido para forçar a sincronização manual;
- ajustar `requirements.txt` para Postgres e adicionar instruções completas do Alembic;
- adicionar um `docker-compose.yml` com Postgres para ambiente local.
