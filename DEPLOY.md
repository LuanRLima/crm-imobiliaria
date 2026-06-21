# Deploy

## Pré-requisitos

- CI verde no workflow `CI`
- segredos de produção/staging configurados fora do repositório
- ambiente `staging` e ambiente `production` criados no GitHub com approval manual para produção

---

## Deploy com backend no Render e frontend no GitHub Pages

O repositório inclui `render.yaml` apenas para o banco e o backend. O frontend
é publicado gratuitamente no GitHub Pages pelo workflow
`.github/workflows/deploy.yml` depois que a CI passa na `master`.

### 1. Crie uma conta no Render

Acesse <https://render.com> e crie uma conta gratuita para o banco PostgreSQL
e o backend Python.

### 2. Conecte o repositório

1. No painel do Render, clique em **New → Blueprint**.
2. Autorize o acesso ao GitHub e selecione o repositório `crm-imobiliaria`.
3. O Render detecta o `render.yaml` automaticamente e lista dois serviços:
   `crm-imobiliaria-db` e `crm-imobiliaria-backend`.

### 3. Defina os segredos obrigatórios

Antes de confirmar o deploy, preencha as variáveis marcadas como `sync: false`:

| Serviço | Variável              | O que colocar                                                         |
|---------|-----------------------|-----------------------------------------------------------------------|
| backend | `SEED_ADMIN_PASSWORD` | Uma senha forte (mín. 8 chars, letras + números + especial)           |
| backend | `CORS_ORIGINS`        | URL do frontend no GitHub Pages — preencha **após** o primeiro deploy |

**Ordem sugerida:**
1. Deploy o banco e o backend primeiro (deixe `CORS_ORIGINS` em branco por ora).
2. Copie a URL pública do backend (ex.: `https://crm-imobiliaria-backend.onrender.com`).
3. No GitHub, crie a variável `FRONTEND_API_URL` com o valor `https://crm-imobiliaria-backend.onrender.com/api/v1`.
4. Publique o frontend no GitHub Pages.
5. Copie a URL pública do frontend (ex.: `https://luanrlima.github.io/crm-imobiliaria`).
6. Preencha `CORS_ORIGINS` no backend com essa URL e reimplante o backend.

### 4. Credenciais de acesso

Após o primeiro deploy bem-sucedido:

- **URL da API:** `https://crm-imobiliaria-backend.onrender.com/docs` (Swagger interativo)
- **E-mail:** `admin@crmimobiliaria.local`
- **Senha:** o valor de `SEED_ADMIN_PASSWORD` que você definiu

### 5. Deploy automático via GitHub Actions

O workflow `.github/workflows/deploy.yml` dispara automaticamente toda vez
que o workflow `CI` passa na branch `master`. Ele faz duas coisas:

- chama o deploy hook do backend no Render
- recompila o frontend e publica no GitHub Pages

Para ativá-lo:

1. No GitHub, vá em **Settings → Pages** e selecione **Build and deployment → Source → GitHub Actions**.
2. No painel do backend no Render, vá em **Settings → Deploy Hook** e copie a URL gerada.
3. No GitHub, configure o hook do backend em **um** destes locais:
   - **Recomendado:** **Settings → Environments → `master - crm-imobiliaria-backend` → Secrets** → **Secret** `RENDER_BACKEND_DEPLOY_HOOK`
   - **Alternativa:** **Settings → Secrets and variables → Actions** → **Secret** `RENDER_BACKEND_DEPLOY_HOOK`
4. Ainda em **Settings → Secrets and variables → Actions**, adicione:
   - **Variable** `BACKEND_PUBLIC_URL` → URL pública do backend sem `/api/v1` (ex.: `https://crm-imobiliaria-backend.onrender.com`)
   - **Variable** `FRONTEND_API_URL` → URL pública do backend + `/api/v1`
   - **Variable** `PAGES_BASE_PATH` → opcional; use apenas se o frontend precisar publicar em um subdiretório diferente do padrão `/<repositório>/`. Em custom domain, deixe em branco ou use `/`.

A partir daí, todo merge na `master` com CI verde dispara o deploy automaticamente.

Depois do publish, o workflow também executa um job `Validate Deploy` para:

- aguardar o backend responder em `BACKEND_PUBLIC_URL/health`
- confirmar que o website publicado no GitHub Pages carregou o HTML esperado

Se quiser a explicação completa das variáveis, da ordem de configuração e dos smoke tests locais/pós-deploy, consulte `VALIDACAO_DEPLOY_URLS_E_TESTES.md`.

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
- O GitHub Pages publica o frontend em `https://<usuario>.github.io/<repositorio>`.
- Para usar o GitHub Pages sem custo, deixe o repositório público.
- Para uso contínuo, considere migrar o backend para um plano pago ou outro host se precisar de mais disponibilidade.

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

## Proteções obrigatórias na `master`

Configure em **Settings → Branches → Branch protection rules**:

- exigir sucesso do workflow `CI` antes do merge
- bloquear merge quando qualquer status check obrigatório falhar
- restringir merge direto na `master` para passar sempre por pull request

## Segredos

Nunca use os valores de `.env.example` em ambientes compartilhados. Para staging e produção, injete `SEED_ADMIN_PASSWORD`, credenciais de banco e demais variáveis via GitHub Secrets ou secret manager equivalente.
