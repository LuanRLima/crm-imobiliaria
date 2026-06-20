import { useEffect, useState } from "react"

import {
  createLead,
  fetchCurrentUser,
  fetchLeads,
  fetchPipelineBoard,
  fetchPipelineStages,
  login,
  moveLeadToStage,
} from "./api/client"
import { LoginForm } from "./features/auth/LoginForm"
import { LeadList } from "./features/leads/LeadList"
import { PipelineBoard } from "./features/pipeline/PipelineBoard"
import type { Lead, PipelineBoard as PipelineBoardType, PipelineStage, User } from "./types"
import "./App.css"

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("crm-token"))
  const [user, setUser] = useState<User | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [stages, setStages] = useState<PipelineStage[]>([])
  const [board, setBoard] = useState<PipelineBoardType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadDashboardData(currentToken: string) {
    return Promise.all([
      fetchCurrentUser(currentToken),
      fetchLeads(currentToken),
      fetchPipelineStages(currentToken),
      fetchPipelineBoard(currentToken),
    ])
  }

  async function refreshData(currentToken: string) {
    const [currentUser, leadList, pipelineStages, pipelineBoard] =
      await loadDashboardData(currentToken)

    setUser(currentUser)
    setLeads(leadList)
    setStages(pipelineStages)
    setBoard(pipelineBoard)
  }

  useEffect(() => {
    if (!token) {
      return
    }

    let isMounted = true

    void (async () => {
      try {
        const [currentUser, leadList, pipelineStages, pipelineBoard] =
          await loadDashboardData(token)

        if (!isMounted) {
          return
        }

        setUser(currentUser)
        setLeads(leadList)
        setStages(pipelineStages)
        setBoard(pipelineBoard)
      } catch (requestError) {
        if (!isMounted) {
          return
        }

        setError((requestError as Error).message)
        setToken(null)
        localStorage.removeItem("crm-token")
      }
    })()

    return () => {
      isMounted = false
    }
  }, [token])

  return (
    <main className="layout">
      <header className="hero">
        <div>
          <p className="eyebrow">CRM Imobiliária · MVP Evolutivo</p>
          <h1>Captação, funil e atendimentos em uma base única</h1>
          <p>
            Esqueleto inicial com autenticação básica, leads e pipeline para acelerar o MVP.
          </p>
        </div>
        {user ? (
          <button
            className="secondary-button"
            onClick={() => {
              localStorage.removeItem("crm-token")
              setUser(null)
              setToken(null)
            }}
            type="button"
          >
            Sair
          </button>
        ) : null}
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      {!token ? (
        <LoginForm
          loading={loading}
          onSubmit={async (email, password) => {
            setLoading(true)
            setError(null)
            try {
              const response = await login(email, password)
              localStorage.setItem("crm-token", response.access_token)
              setToken(response.access_token)
              setUser(response.user)
            } catch (requestError) {
              setError((requestError as Error).message)
            } finally {
              setLoading(false)
            }
          }}
        />
      ) : (
        <>
          <section className="card user-card">
            <strong>{user?.name}</strong>
            <span>
              {user?.role} · {user?.email}
            </span>
          </section>

          <div className="dashboard-grid">
            <LeadList
              leads={leads}
              stages={stages}
              onCreateLead={async (payload) => {
                if (!token) {
                  return
                }
                await createLead(token, payload)
                await refreshData(token)
              }}
              onMoveLead={async (leadId, stageId) => {
                if (!token) {
                  return
                }
                await moveLeadToStage(token, leadId, stageId)
                await refreshData(token)
              }}
            />
            <PipelineBoard board={board} />
          </div>
        </>
      )}
    </main>
  )
}

export default App
