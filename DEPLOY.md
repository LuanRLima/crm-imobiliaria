# Deploy

## Pré-requisitos

- CI verde no workflow `CI`
- segredos de produção/staging configurados fora do repositório
- ambiente `staging` e ambiente `production` criados no GitHub com approval manual para produção

---

## Deploy no Render (recomendado para testar rapidamente)

O repositório inclui `render.yaml` com todos os serviços declarados — basta
conectar o repositório no Render e preencher dois segredos.

### 1. Crie uma conta no Render

Acesse <https://render.com> e crie uma conta gratuita (plano Free inclui
banco PostgreSQL, backend Python e frontend estático).

### 2. Conecte o repositório

1. No painel do Render, clique em **New → Blueprint**.
2. Autorize o acesso ao GitHub e selecione o repositório `crm-imobiliaria`.
3. O Render detecta o `render.yaml` automaticamente e lista os três serviços:
   `crm-imobiliaria-db`, `crm-imobiliaria-backend` e `crm-imobiliaria-frontend`.

### 3. Defina os segredos obrigatórios

Antes de confirmar o deploy, preencha as variáveis marcadas como `sync: false`:

| Serviço  | Variável               | O que colocar                                                  |
|----------|------------------------|----------------------------------------------------------------|
| backend  | `SEED_ADMIN_PASSWORD`  | Uma senha forte (mín. 8 chars, letras + números + especial)    |
| backend  | `CORS_ORIGINS`         | URL do frontend — preencha **após** o primeiro deploy do front |
| frontend | `VITE_API_URL`         | URL do backend + `/api/v1` — preencha após o deploy do backend |

**Ordem sugerida:**
1. Deploy o banco e o backend primeiro (deixe `CORS_ORIGINS` em branco por ora).
2. Copie a URL pública do backend (ex.: `https://crm-imobiliaria-backend.onrender.com`).
3. Preencha `VITE_API_URL` no frontend como `https://crm-imobiliaria-backend.onrender.com/api/v1`.
4. Copie a URL pública do frontend (ex.: `https://crm-imobiliaria-frontend.onrender.com`).
5. Preencha `CORS_ORIGINS` no backend com essa URL e reimplante o backend.

### 4. Credenciais de acesso

Após o primeiro deploy bem-sucedido:

- **URL da API:** `https://crm-imobiliaria-backend.onrender.com/docs` (Swagger interativo)
- **E-mail:** `admin@crmimobiliaria.local`
- **Senha:** o valor de `SEED_ADMIN_PASSWORD` que você definiu

### 5. Deploy automático via GitHub Actions

O workflow `.github/workflows/deploy.yml` dispara automaticamente toda vez
que o workflow `CI` passa na branch `main`. Para ativá-lo:

1. No painel de cada serviço Render, vá em **Settings → Deploy Hook** e copie
   a URL gerada.
2. No repositório GitHub, vá em **Settings → Secrets and variables → Actions**
   e adicione:
   - `RENDER_BACKEND_DEPLOY_HOOK` → URL do hook do backend
   - `RENDER_FRONTEND_DEPLOY_HOOK` → URL do hook do frontend

A partir daí, todo merge na `main` com CI verde dispara o deploy automaticamente.

### Limitações do plano gratuito

- O banco PostgreSQL gratuito **expira após 90 dias** — faça backup antes com:
  ```bash
  pg_dump "$(render env get DATABASE_URL --service crm-imobiliaria-backend)" \
    > backup_$(date +%Y%m%d).sql
  ```
  Ou pelo painel: **Dashboard → crm-imobiliaria-db → Backups**.
  Consulte a [documentação de backups do Render](https://render.com/docs/postgresql-backups) para mais detalhes.
- O backend pode **adormecer** após 15 min de inatividade (primeira requisição
  pode demorar ~30 s para acordar).
- Para uso contínuo, considere o plano pago ($7/mês por serviço).

---

## Staging

1. Atualize as variáveis do backend e frontend com valores do ambiente de staging.
2. Gere a imagem/artefato a partir do commit validado pela CI.
3. Rode `alembic upgrade head` no banco de staging.
4. Publique a nova versão.
5. Valide login, criação de lead, entrada automática no pipeline e movimentação entre etapas.

## Produção

1. Promova apenas commits já validados em staging.
2. Exija aprovação manual no ambiente `production` antes do deploy.
3. Rode `alembic upgrade head` antes de expor a nova versão.
4. Faça smoke test de login, leads e pipeline logo após a publicação.

## Rollback

1. Interrompa o rollout atual.
2. Reimplante o último artefato estável.
3. Se a falha vier de migration incompatível, restaure o backup do banco e só então refaça o deploy da versão anterior.
4. Revalide login e fluxo principal após o rollback.

## Proteções obrigatórias na `main`

Configure em **Settings → Branches → Branch protection rules**:

- exigir sucesso do workflow `CI` antes do merge
- bloquear merge quando qualquer status check obrigatório falhar
- restringir merge direto na `main` para passar sempre por pull request

## Segredos

Nunca use os valores de `.env.example` em ambientes compartilhados. Para staging e produção, injete `SEED_ADMIN_PASSWORD`, credenciais de banco e demais variáveis via GitHub Secrets ou secret manager equivalente.
