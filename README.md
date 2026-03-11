# WYDRanking

Aplicação web (FastAPI + Jinja2) para visualização e manutenção de rankings de jogadores (level e arena).

## Descrição

Este projeto coleta, processa e apresenta rankings de jogadores (level e arena), incluindo histórico de snapshots e ferramentas administrativas para busca e análise. Possui um atualizador em background que sincroniza dados em horários programados.

## Recursos

- Ranking de Level (com mudanças de nível)
- Ranking de Arena (categorias `champion` e `aspirant`)
- Histórico de rankings e snapshots diários
- Autenticação simples com usuário admin padrão
- UI baseada em templates Jinja2

## Requisitos

- Python 3.9+ recomendado
- Dependências em `requirements.txt`

Instalar dependências:

```bash
pip install -r requirements.txt
```


## Configuração e banco de dados

- O projeto utiliza apenas Postgres (não há mais fallback para SQLite).
- Para criar as tabelas, execute o script `create_tables.py` ou deixe o evento de startup criar automaticamente.

```bash
python create_tables.py
```

- O primeiro startup cria um usuário admin padrão (username: `admin`, password: `admin123`) caso não exista.

**Arquivos obsoletos removidos:**
- `app.db` (SQLite antigo)
- `data_backup.json` (backup antigo)
- Todas as pastas `__pycache__` (cache Python)

**Apenas arquivos essenciais permanecem no projeto.**

## Executando a aplicação

Executar com Uvicorn (recomendado para desenvolvimento):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ou usando o módulo python:

```bash
python -m uvicorn app.main:app --reload
```

Depois, abra `http://localhost:8000` no navegador.

## Estrutura do projeto (visão geral)

- `app/` — código da aplicação
  - `main.py` — FastAPI app e rotas
  - `database.py` — configuração do SQLAlchemy/engine
  - `models.py` — modelos ORM
  - `repositories/` — acesso aos dados
  - `services/` — lógica de negócio, sincronização e autenticação
  - `templates/` — templates Jinja2 para as páginas
  - `static/` — CSS e JS estáticos
- `create_tables.py` — script para criar tabelas
- `requirements.txt` — dependências Python
- `scripts/` — ferramentas utilitárias (ex.: `db_inspect.py`)

## Scripts úteis

- `create_tables.py` — cria as tabelas do banco.
- `scripts/db_inspect.py` — ferramentas para inspecionar o DB (verificar conteúdo / snapshots).

## Desenvolvimento

- Recomenda-se criar um virtualenv e instalar dependências.
- Para desenvolvimento local, rode com `uvicorn` conforme instruções acima.

## Contribuição

1. Fork o repositório
2. Crie uma branch com sua feature: `git checkout -b feature/nome`
3. Abra um pull request descrevendo as mudanças

## Contato

Para dúvidas ou sugestões, abra uma issue no repositório ou entre em contato com o mantenedor do projeto.

## Licença

Licença não especificada — adicione uma licença apropriada se necessário.

## Deploy no Render (passo-a-passo)

1) Preparar o repositório

- Commit e push do código para um repositório Git (GitHub/GitLab). O Render irá conectar ao repositório.

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your_repo_url>
git push -u origin main
```

2) Arquivos incluídos para o Render

- `Dockerfile` — define a imagem do container.
- `start.sh` — cria tabelas (`create_tables.py`) e inicia o servidor Uvicorn. O script inicia com `--workers 1` para evitar múltiplas instâncias do updater em background.

3) Banco de dados

- Recomendo usar um banco Postgres gerenciado (o Render oferece um add-on Postgres). Crie uma instância Postgres no painel do Render e copie a `DATABASE_URL` (algo como `postgresql://user:pass@host:port/dbname`).
- No painel do serviço Web no Render, adicione a variável de ambiente `DATABASE_URL` com o valor provido pelo Postgres.

4) Criar novo serviço Web no Render

- Acesse https://render.com e crie uma conta caso necessário.
- Clique em "New" → "Web Service" → conecte seu repositório.
- Escolha o branch (ex.: `main`) e selecione o método de build: `Docker` (o Render detectará o `Dockerfile`).
- Para o comando de build/deploy, deixe o padrão (Render usará Dockerfile). Para a porta, o container lê a variável `PORT` (definida automaticamente pelo Render).
- Em "Environment", escolha `Docker` ou `Managed` conforme UI do Render.

5) Variáveis de ambiente recomendadas

- `DATABASE_URL` — (obrigatória) string de conexão Postgres.
- `PORT` — normalmente o Render fornece automaticamente; não é necessário setar manualmente.

6) Observações importantes

- O app usa um thread de background no `startup` (`background_updater`). Para evitar múltiplas execuções simultâneas desse thread, o `start.sh` inicia o Uvicorn com `--workers 1`. Se precisar de mais concorrência, transforme o job de sincronização em um worker separado (ex.: cron, Celery, ou serviço de background no Render) antes de aumentar `--workers`.
- `start.sh` executa `python create_tables.py` no início. Isso é simples para garantir que as tabelas existam. Em ambientes mais maduros, prefira migrations (Alembic).

7) Deploy e verificação

- Após criar o serviço, clique em "Manual Deploy" ou aguarde o deploy automático ao push.
- No painel do serviço, verifique os logs para ver a saída do `create_tables.py` e do Uvicorn.
- Acesse a URL pública fornecida pelo Render.

8) Se algo falhar

- Verifique os logs no painel do Render.
- Confirme `DATABASE_URL` e credenciais.
- Se houver erro na instalação de dependências (p.ex. `psycopg`), assegure que o `Dockerfile` instala `libpq-dev` e `build-essential` (já incluído).

Se quiser, eu posso:

- Gerar e commitar o `Dockerfile` e `start.sh` (já feitos), ou
- Gerar um `render.yaml` com serviço e banco configurados, pronto para `render up` (posso criar se desejar), ou
- Guiar passo-a-passo enquanto você publica (posso acompanhar cada passo hoje).

