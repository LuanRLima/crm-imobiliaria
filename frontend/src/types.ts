export type User = {
  id: number
  name: string
  email: string
  role: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  expires_at: string
  user: User
}

export type Lead = {
  id: number
  name: string
  email?: string | null
  phone?: string | null
  source: string
  status: string
  notes?: string | null
  broker_id?: number | null
  current_stage?: string | null
  created_at: string
  updated_at: string
}

export type PipelineLeadSummary = {
  id: number
  name: string
  source: string
}

export type PipelineStage = {
  id: number
  name: string
  position: number
  is_active: boolean
  leads?: PipelineLeadSummary[]
}

export type PipelineBoard = {
  stages: PipelineStage[]
}
