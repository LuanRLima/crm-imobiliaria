import { expect, test } from "@playwright/test"

const apiUrl = (process.env.E2E_API_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "")
const healthUrl =
  process.env.E2E_HEALTH_URL ?? `${apiUrl.replace(/\/api\/v1$/, "")}/health`
const adminEmail = process.env.E2E_ADMIN_EMAIL ?? "admin@crmimobiliaria.local"
const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? "changeme"

test("backend mantém o fluxo principal de negócio", async ({ request }) => {
  const leadName = `Smoke API ${Date.now()}`

  const healthResponse = await request.get(healthUrl)
  expect(healthResponse.ok()).toBeTruthy()
  await expect(healthResponse.json()).resolves.toEqual({ status: "ok" })

  const loginResponse = await request.post(`${apiUrl}/auth/login`, {
    data: {
      email: adminEmail,
      password: adminPassword,
    },
  })
  expect(loginResponse.ok()).toBeTruthy()

  const loginPayload = (await loginResponse.json()) as { access_token: string }
  const headers = {
    Authorization: "Bearer " + loginPayload.access_token,
  }

  const createLeadResponse = await request.post(`${apiUrl}/leads`, {
    data: {
      name: leadName,
      email: `smoke-api-${Date.now()}@example.com`,
      source: "smoke-api",
    },
    headers,
  })
  expect(createLeadResponse.status()).toBe(201)

  const createdLead = (await createLeadResponse.json()) as {
    current_stage: string
    id: number
  }
  expect(createdLead.current_stage).toBe("Novo Lead")

  const stagesResponse = await request.get(`${apiUrl}/pipeline/stages`, { headers })
  expect(stagesResponse.ok()).toBeTruthy()

  const stages = (await stagesResponse.json()) as Array<{ id: number; name: string }>
  const targetStage = stages.find((stage) => stage.name === "Contato Realizado")
  expect(targetStage).toBeDefined()

  const moveLeadResponse = await request.post(
    `${apiUrl}/pipeline/leads/${createdLead.id}/move`,
    {
      data: { stage_id: targetStage?.id },
      headers,
    },
  )
  expect(moveLeadResponse.ok()).toBeTruthy()

  const boardResponse = await request.get(`${apiUrl}/pipeline/board`, { headers })
  expect(boardResponse.ok()).toBeTruthy()

  const board = (await boardResponse.json()) as {
    stages: Array<{ leads: Array<{ name: string }>; name: string }>
  }
  const movedStage = board.stages.find((stage) => stage.name === "Contato Realizado")

  expect(movedStage?.leads.some((lead) => lead.name === leadName)).toBeTruthy()
})

test("frontend carrega login, cria lead e atualiza o pipeline", async ({ page }) => {
  const leadName = `Smoke UI ${Date.now()}`

  await page.goto("/")

  await expect(
    page.getByRole("heading", { name: "Captação, funil e atendimentos em uma base única" }),
  ).toBeVisible()

  await page.getByLabel("E-mail").fill(adminEmail)
  await page.getByLabel("Senha").fill(adminPassword)
  await page.getByRole("button", { name: "Entrar" }).click()

  await expect(page.getByText(adminEmail)).toBeVisible()

  await page.getByLabel("Nome").fill(leadName)
  await page.getByLabel("Telefone").fill("11999999999")
  await page.getByLabel("Origem").fill("smoke-ui")
  await page.getByLabel("Observações").fill("Validação automatizada pós-build")
  await page.getByRole("button", { name: "Salvar lead" }).click()

  const leadItem = page.locator(".lead-item").filter({ hasText: leadName })
  await expect(leadItem).toContainText("Novo Lead")

  await leadItem.locator("select").selectOption({ label: "Contato Realizado" })

  const movedCard = page
    .locator(".pipeline-stage")
    .filter({ hasText: "Contato Realizado" })
    .locator(".pipeline-card")
    .filter({ hasText: leadName })

  await expect(movedCard).toBeVisible()
})
