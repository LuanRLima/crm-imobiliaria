# Deploy

## Pré-requisitos

- CI verde no workflow `CI`
- segredos de produção/staging configurados fora do repositório
- ambiente `staging` e ambiente `production` criados no GitHub com approval manual para produção

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

## Próximo passo planejado

Se a operação pedir deploy automatizado, adicione um workflow dedicado como `.github/workflows/deploy-staging.yml`, mantendo approval manual para produção.
