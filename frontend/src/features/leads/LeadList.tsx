import { useMemo, useState } from "react"

import type { Lead, PipelineStage } from "../../types"

type LeadListProps = {
  leads: Lead[]
  stages: PipelineStage[]
  onCreateLead: (payload: {
    name: string
    email?: string
    phone?: string
    source: string
    notes?: string
  }) => Promise<void>
  onMoveLead: (leadId: number, stageId: number) => Promise<void>
}

const defaultForm = {
  name: "",
  email: "",
  phone: "",
  source: "site",
  notes: "",
}

export function LeadList({ leads, stages, onCreateLead, onMoveLead }: LeadListProps) {
  const [form, setForm] = useState(defaultForm)
  const stageByName = useMemo(
    () => new Map(stages.map((stage) => [stage.name, stage.id])),
    [stages],
  )

  return (
    <section className="column">
      <div className="card form-card">
        <h2>Novo lead</h2>
        <label>
          Nome
          <input
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
        </label>
        <label>
          E-mail
          <input
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            type="email"
          />
        </label>
        <label>
          Telefone
          <input
            value={form.phone}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
          />
        </label>
        <label>
          Origem
          <input
            value={form.source}
            onChange={(event) => setForm({ ...form, source: event.target.value })}
          />
        </label>
        <label>
          Observações
          <textarea
            value={form.notes}
            onChange={(event) => setForm({ ...form, notes: event.target.value })}
          />
        </label>
        <button
          onClick={async () => {
            await onCreateLead({
              name: form.name,
              email: form.email || undefined,
              phone: form.phone || undefined,
              source: form.source,
              notes: form.notes || undefined,
            })
            setForm(defaultForm)
          }}
          type="button"
        >
          Salvar lead
        </button>
      </div>

      <div className="card">
        <h2>Leads cadastrados</h2>
        <div className="lead-list">
          {leads.map((lead) => (
            <article key={lead.id} className="lead-item">
              <div>
                <strong>{lead.name}</strong>
                <p>{lead.email ?? lead.phone}</p>
                <small>
                  {lead.source} · {lead.current_stage ?? "Sem etapa"}
                </small>
              </div>
              <select
                defaultValue={stageByName.get(lead.current_stage ?? "")}
                onChange={(event) => onMoveLead(lead.id, Number(event.target.value))}
              >
                {stages.map((stage) => (
                  <option key={stage.id} value={stage.id}>
                    {stage.name}
                  </option>
                ))}
              </select>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
