import type { Lead, LoginResponse, PipelineBoard, PipelineStage, User } from "../types"

const apiUrlFromEnv = import.meta.env.VITE_API_URL?.trim()
const API_URL = apiUrlFromEnv && apiUrlFromEnv.length > 0 ? apiUrlFromEnv : "http://localhost:8000/api/v1"

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH"
  token?: string | null
  body?: unknown
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: "Bearer " + options.token } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Erro inesperado." }))
    throw new Error(error.detail ?? "Erro inesperado.")
  }

  return response.json() as Promise<T>
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
  })
}

export function fetchCurrentUser(token: string): Promise<User> {
  return request<User>("/auth/me", { token })
}

export function fetchLeads(token: string): Promise<Lead[]> {
  return request<Lead[]>("/leads", { token })
}

export function createLead(
  token: string,
  payload: { name: string; email?: string; phone?: string; source: string; notes?: string },
): Promise<Lead> {
  return request<Lead>("/leads", {
    method: "POST",
    token,
    body: payload,
  })
}

export function fetchPipelineStages(token: string): Promise<PipelineStage[]> {
  return request<PipelineStage[]>("/pipeline/stages", { token })
}

export function fetchPipelineBoard(token: string): Promise<PipelineBoard> {
  return request<PipelineBoard>("/pipeline/board", { token })
}

export function moveLeadToStage(
  token: string,
  leadId: number,
  stageId: number,
): Promise<PipelineStage> {
  return request<PipelineStage>(`/pipeline/leads/${leadId}/move`, {
    method: "POST",
    token,
    body: { stage_id: stageId },
  })
}
