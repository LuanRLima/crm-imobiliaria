# CRM Imobiliária · MVP evolutivo

Projeto inicial de um CRM para imobiliária com foco em captação de leads, funil comercial, acompanhamento operacional e dashboards futuros. O repositório estava vazio; por isso, a implementação abaixo cria o esqueleto inicial completo do MVP com **frontend React + Vite**, **backend FastAPI**, **PostgreSQL**, **Alembic**, **Docker Compose** e **testes iniciais**.

## 1) Visão do produto

### Problema que resolve
- Centraliza captação de leads vindos de site, portais e WhatsApp.
- Organiza o funil comercial de venda/aluguel com rastreabilidade por etapa.
- Dá visibilidade de atendimento, tempo de resposta e evolução até fechamento.
- Reduz perda de oportunidades por falta de follow-up e distribuição manual.

### Perfis de usuário
- **Gestor:** acompanha metas, conversão, tempo de resposta, carga por corretor.
- **Corretor:** recebe leads, registra contatos, visitas, propostas e próximos passos.
- **Atendimento/SDR:** triagem inicial, enriquecimento do lead e distribuição.

### MVP vs futuras versões
**MVP**
- Login básico por perfil.
- Cadastro de leads.
- Pipeline configurável em etapas iniciais.
- Visualização simples do board comercial.
- Distribuição manual/assistida de leads.
- Base para auditoria e relatórios operacionais.

**Futuras versões**
- Integração com WhatsApp, portais e discador.
- Agenda completa com visitas e lembretes automáticos.
- Relatórios avançados e dashboards por equipe/origem.
- SLA de atendimento, automações, campanhas e omnichannel.
- LGPD avançada: consentimento, anonimização e retenção.

## 2) Requisitos funcionais

- **Cadastro de imóveis:** backlog da próxima fase; ainda não implementado no esqueleto.
- **Cadastro de clientes/leads:** implementado via API e UI inicial.
- **Pipeline de vendas:** etapas configuráveis, board e movimentação de lead.
- **Histórico de atendimento:** modelagem preparada via auditoria; interações detalhadas ficam para evolução.
- **Agenda e lembretes:** campo `next_action_at` já previsto no pipeline.
- **Distribuição de leads:** `broker_id` e `assigned_to_id` já previstos no domínio.
- **Relatórios básicos:** previstos como próximo incremento sobre audit logs e lead sources.

## 3) Requisitos não funcionais

- **Segurança:** autenticação bearer básica, segregação por perfil no modelo de usuário, seeds de desenvolvimento e orientação LGPD para evolução.
- **Auditoria:** tabela `audit_logs` já criada para trilha de alterações.
- **Performance:** foco em consultas simples com índices naturais/uniques e estrutura suficiente para uso diário no MVP.
- **Observabilidade:** endpoint `/health` implementado; logs estruturados e métricas entram na próxima iteração.

## 4) Arquitetura sugerida (Clean Architecture)

### Camadas
- **Frontend:** React/Vite com componentes por feature.
- **Backend:** FastAPI com rotas, schemas, serviços e camada de persistência separadas.
- **Banco:** PostgreSQL para ambiente local e produção inicial.
- **Mensageria:** adiada no MVP para evitar overengineering; considerar fila só quando integrações assíncronas crescerem.

### Organização de pastas

```text
backend/
  app/
    api/
    core/
    db/
    schemas/
    services/
  alembic/
  tests/
frontend/
  src/
    api/
    features/
docker-compose.yml
```

### Estratégias
- **Versionamento de API:** prefixo `/api/v1`.
- **Erros e validação:** validação com Pydantic/FastAPI; respostas 401, 404, 409 e 422 padronizadas.
- **Trade-off:** autenticação por sessão bearer persistida em banco é mais simples para MVP que um fluxo OAuth/JWT completo.

## 5) Stack recomendada (com justificativa)

- **Frontend escolhido:** **React + Vite + TypeScript**
  - alta velocidade de entrega, baixo custo cognitivo e ótimo ecossistema para dashboards futuros.
- **Backend escolhido:** **FastAPI**
  - rápido para MVP, tipado, fácil testar e documentar.
- **Banco de dados:** **PostgreSQL**
  - consistente para CRM, bom suporte relacional e pronto para relatórios.
- **Cache:** não implementado no MVP inicial; Redis entra quando houver pressão real de leitura/sessão.
- **Fila:** não necessária no primeiro corte.
- **Autenticação:** bearer token persistido em `auth_sessions`, suficiente para ambiente inicial.

## 6) Modelagem inicial de domínio

### Entidades principais
- **User**
- **AuthSession**
- **Lead**
- **PipelineStage**
- **PipelineEntry**
- **AuditLog**

### Relacionamentos
- 1 usuário → N sessões
- 1 lead → 1 entrada de pipeline
- 1 etapa → N entradas
- lead pode referenciar corretor responsável
- audit log pode referenciar ator responsável

### Estados iniciais do funil
1. Novo Lead
2. Contato Realizado
3. Visita Agendada
4. Proposta
5. Fechado

### Regras críticas
- lead precisa ter ao menos e-mail ou telefone.
- todo lead novo entra automaticamente na primeira etapa ativa do pipeline.
- movimentação só aceita etapas ativas.
- seeds criam um admin técnico e etapas padrão para ambiente local.

## 7) API inicial (MVP)

### Endpoints essenciais

#### `POST /api/v1/auth/login`
Request:
```json
{
  "email": "admin@crmimobiliaria.local",
  "password": "Admin123!"
}
```

Response:
```json
{
  "access_token": "token",
  "token_type": "bearer",
  "expires_at": "2026-06-20T18:00:00Z",
  "user": {
    "id": 1,
    "name": "Administrador",
    "email": "admin@crmimobiliaria.local",
    "role": "manager"
  }
}
```

#### `POST /api/v1/auth/logout`
Revoga a sessão atual do bearer token autenticado.

#### `POST /api/v1/leads`
```json
{
  "name": "Maria Cliente",
  "email": "maria@cliente.com",
  "source": "landing-page",
  "notes": "Quer apartamento com 3 quartos"
}
```

#### `GET /api/v1/pipeline/board`
Retorna board agrupado por etapa.

#### `POST /api/v1/pipeline/leads/{lead_id}/move`
```json
{
  "stage_id": 2
}
```

### Regras de validação
- e-mail válido quando informado.
- telefone ou e-mail é obrigatório no lead.
- login exige credenciais válidas.
- login aplica rate limit por cliente/e-mail após falhas repetidas.
- criação de etapa é restrita ao perfil `manager`.

### Códigos de erro padrão
- `401` autenticação inválida.
- `403` operação sem permissão.
- `404` recurso não encontrado.
- `429` muitas tentativas de login.
- `409` conflito de negócio/configuração.
- `422` payload inválido.

## 8) Estratégia de testes

- **Unitários:** regras de segurança, validações e serviços.
- **Integração:** login, criação de lead, listagem e movimentação no pipeline.
- **E2E:** próximo passo com Playwright/Cypress quando fluxos de UI amadurecerem.
- **Primeiros cenários implementados agora:**
  - healthcheck
  - login com sucesso/erro
  - cadastro/listagem de leads
  - movimentação entre etapas
- **Ferramentas:** `pytest` no backend; frontend ainda sem runner de testes para evitar dependências desnecessárias no primeiro corte.

## 9) Plano de execução em 12 semanas

### Fase 1 (semanas 1-4) · fundação
- **Entregas:** autenticação, base de usuários, leads, pipeline, Docker, migrations, testes iniciais.
- **Riscos:** escopo amplo demais cedo, modelagem prematura.
- **Critérios de aceite:** API sobe localmente, login funciona, lead percorre pipeline.

### Fase 2 (semanas 5-8) · MVP funcional
- **Entregas:** imóveis, agenda, histórico de atendimento, distribuição automatizada, relatórios básicos.
- **Riscos:** integrações externas e inconsistência operacional.
- **Critérios de aceite:** corretor consegue atender e avançar oportunidade fim a fim.

### Fase 3 (semanas 9-12) · melhorias e escala
- **Entregas:** dashboards, observabilidade, LGPD avançada, automações, integrações.
- **Riscos:** custo operacional, acoplamento com canais externos.
- **Critérios de aceite:** gestão acompanha funil e produtividade com confiabilidade.

## 10) DevEx / qualidade

- **Lint/format**
  - Frontend: ESLint já configurado.
  - Backend: manter estilo simples e padronizar com Ruff/Black na próxima iteração.
- **Hooks de commit:** sugerido `pre-commit` com lint/test parcial no próximo incremento.
- **Template de PR:** incluir objetivo, evidências, riscos e checklist de testes.
- **Checklist de code review**
  - regra de negócio coberta?
  - autorização/autenticação preservadas?
  - migration compatível?
  - erros e mensagens claras?
  - impacto LGPD conhecido?
- **Pipeline CI básico:** recomendado rodar `pytest`, `npm run lint` e `npm run build`.

## 11) Próximo passo prático

### Estrutura inicial gerada
- monorepo com `backend/` e `frontend/`
- autenticação básica
- módulo de leads
- módulo de pipeline
- migrations iniciais
- testes iniciais
- `docker-compose.yml`

### Backlog inicial

#### Épicos
1. Fundação da plataforma
2. CRM comercial
3. Atendimento e agenda
4. Imóveis e matching
5. Relatórios e performance

#### Histórias e tarefas iniciais
- Como gestor, quero autenticar usuários por perfil.
- Como atendimento, quero cadastrar e qualificar leads.
- Como corretor, quero mover leads no pipeline.
- Como gestor, quero auditar alterações críticas.
- Como time, quero subir ambiente local com um comando.

### 10 primeiras issues para GitHub
1. **Criar cadastro de imóveis**
   - descrição: modelar imóvel, endereço, tipologia, preço e status.
   - aceite: CRUD com validações mínimas.
2. **Adicionar histórico de atendimento**
   - aceite: registrar ligação, WhatsApp, visita e proposta por lead.
3. **Implementar agenda e lembretes**
   - aceite: próximos passos visíveis por corretor.
4. **Distribuição automática de leads**
   - aceite: regra round-robin ou por região/carteira.
5. **Criar dashboard de conversão**
   - aceite: taxa por origem e por etapa.
6. **Adicionar RBAC por perfil**
   - aceite: gestor, corretor e atendimento com permissões distintas.
7. **Integrar captação via landing page**
   - aceite: endpoint público com proteção anti-spam básica.
8. **Adicionar observabilidade**
   - aceite: logs estruturados e métricas HTTP.
9. **Criar pipeline CI**
   - aceite: lint, build e testes automáticos em PR.
10. **Preparar LGPD operacional**
    - aceite: consentimento, anonimização e política de retenção inicial.

## Como executar

### Opção 1 · Docker Compose
```bash
docker compose up --build
```

Serviços:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Docs interativas: http://localhost:8000/docs

### Opção 2 · Desenvolvimento local

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Credenciais seed
- E-mail: `admin@crmimobiliaria.local`
- Senha: `Admin123!`

> Use essas credenciais apenas para ambiente local. Em produção, substitua por um fluxo de provisionamento seguro.

## Testes e validação

### Backend
```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### Frontend
```bash
cd frontend
npm install
npm run lint
npm run build
```
