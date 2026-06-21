# Validação de deploy, URLs e website

Este arquivo explica como configurar as URLs do backend/frontend e como funcionam
as validações automatizadas para garantir que o deploy, os endpoints e as telas
principais continuem funcionando.

## 1. O que cada URL faz

### `BACKEND_PUBLIC_URL`
- Exemplo: `https://crm-imobiliaria-backend.onrender.com`
- Usada no workflow de deploy para esperar o backend publicar com sucesso.
- Deve apontar para a raiz pública do backend, **sem** `/api/v1`.

### `FRONTEND_API_URL`
- Exemplo: `https://crm-imobiliaria-backend.onrender.com/api/v1`
- Usada no build do frontend para definir para qual API o website vai chamar.
- Essa URL entra no `VITE_API_URL`.

### `PAGES_BASE_PATH`
- Exemplo padrão no GitHub Pages: `/crm-imobiliaria/`
- Use `/` se estiver publicando em domínio próprio.
- Se deixar vazio, o workflow usa automaticamente `/<nome-do-repositório>/`.

### `CORS_ORIGINS`
- Exemplo: `https://luanrlima.github.io/crm-imobiliaria`
- Configurada no Render.
- Precisa conter a URL pública do frontend para o navegador conseguir chamar o backend sem bloqueio de CORS.

## 2. Ordem correta de configuração

1. Faça o deploy do backend no Render.
2. Copie a URL pública do backend e salve:
   - `BACKEND_PUBLIC_URL` = raiz do backend
   - `FRONTEND_API_URL` = raiz do backend + `/api/v1`
3. Publique o frontend no GitHub Pages.
4. Copie a URL pública do frontend e configure `CORS_ORIGINS` no backend.
5. Rode um novo deploy do backend para aplicar o CORS correto.

## 3. Onde configurar no GitHub e no Render

### GitHub Actions
Em **Settings → Secrets and variables → Actions**:

**Secrets**
- `RENDER_BACKEND_DEPLOY_HOOK`

**Variables**
- `BACKEND_PUBLIC_URL`
- `FRONTEND_API_URL`
- `PAGES_BASE_PATH` (opcional)

### Render
No serviço do backend:
- `SEED_ADMIN_PASSWORD`
- `CORS_ORIGINS`
- `DATABASE_URL` (normalmente já vem do banco no `render.yaml`)

## 4. O que a CI valida antes do deploy

O workflow `.github/workflows/ci.yml` agora executa:

1. **Backend**
   - `pytest`
   - `alembic upgrade head`
2. **Frontend**
   - `npm run lint`
   - `npm run build`
3. **Smoke Tests**
   - sobe o backend localmente
   - faz o build do frontend apontando para a API local
   - publica o frontend localmente com `vite preview`
   - valida os endpoints principais do backend
   - valida login, criação de lead e movimentação no pipeline pela interface
4. **Security**
   - `pip-audit`
   - `npm audit --omit=dev`

## 5. O que o deploy valida depois da publicação

O workflow `.github/workflows/deploy.yml` agora executa o job `Validate Deploy`:

1. espera o backend responder em `BACKEND_PUBLIC_URL/health`
2. valida que o GitHub Pages publicou o HTML do website

Isso ajuda a confirmar que:
- o backend subiu
- o website foi publicado
- as URLs mínimas do deploy estão corretas

## 6. Regras de negócio cobertas pelos smoke tests

Os testes automatizados cobrem o fluxo principal do MVP:

- healthcheck do backend
- login com usuário seed
- criação de lead
- entrada automática em `Novo Lead`
- movimentação do lead para `Contato Realizado`
- atualização visual do pipeline no frontend

## 7. Como rodar localmente

### Backend
```bash
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend
npm ci
VITE_API_URL=http://127.0.0.1:8000/api/v1 npm run build
npm run preview -- --host 127.0.0.1 --port 4173
```

### Smoke tests
Em outro terminal:
```bash
cd frontend
npx playwright install --with-deps chromium
E2E_API_URL=http://127.0.0.1:8000/api/v1 \
E2E_BASE_URL=http://127.0.0.1:4173 \
npm run test:e2e
```

## 8. Se algo falhar

### Backend falhando no deploy
- confira `BACKEND_PUBLIC_URL`
- confira se o Render terminou o deploy
- confira `SEED_ADMIN_PASSWORD`
- confira migration e banco

### Frontend falhando ao chamar a API
- confira `FRONTEND_API_URL`
- confira `CORS_ORIGINS`
- confira `PAGES_BASE_PATH`

### Login funcionando localmente, mas falhando em produção
- confira a senha real configurada em `SEED_ADMIN_PASSWORD`
- confira se o backend recebeu as variáveis atualizadas
- confira se o deploy do backend foi refeito depois da mudança
