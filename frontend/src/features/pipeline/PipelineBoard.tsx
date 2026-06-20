import type { PipelineBoard } from "../../types"

type PipelineBoardProps = {
  board: PipelineBoard | null
}

export function PipelineBoard({ board }: PipelineBoardProps) {
  return (
    <section className="card">
      <h2>Pipeline comercial</h2>
      <div className="pipeline-grid">
        {board?.stages.map((stage) => (
          <div className="pipeline-stage" key={stage.id}>
            <header>
              <strong>{stage.name}</strong>
              <span>{stage.leads?.length ?? 0} leads</span>
            </header>
            <div className="pipeline-cards">
              {stage.leads?.map((lead) => (
                <article className="pipeline-card" key={lead.id}>
                  <strong>{lead.name}</strong>
                  <small>{lead.source}</small>
                </article>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
