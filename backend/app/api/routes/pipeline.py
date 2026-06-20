from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user, get_db, require_roles
from app.db.models import Lead, PipelineEntry, PipelineStage, User
from app.schemas.pipeline import (
    MoveLeadRequest,
    PipelineBoardResponse,
    PipelineLeadSummary,
    PipelineStageCreate,
    PipelineStageResponse,
)
from app.services.audit import register_audit_log

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/stages", response_model=list[PipelineStageResponse])
def list_stages(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PipelineStageResponse]:
    stages = db.scalars(
        select(PipelineStage).order_by(PipelineStage.position.asc())
    ).all()
    return [PipelineStageResponse.model_validate(stage) for stage in stages]


@router.post(
    "/stages",
    response_model=PipelineStageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stage(
    payload: PipelineStageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("manager")),
) -> PipelineStageResponse:
    try:
        stage = PipelineStage(
            name=payload.name,
            position=payload.position,
            is_active=payload.is_active,
        )
        db.add(stage)
        db.flush()
        register_audit_log(
            db,
            actor_id=current_user.id,
            entity="pipeline_stage",
            entity_id=stage.id,
            action="created",
            payload={"name": payload.name, "position": payload.position},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(stage)
    return PipelineStageResponse.model_validate(stage)


@router.get("/board", response_model=PipelineBoardResponse)
def get_board(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PipelineBoardResponse:
    stages = db.scalars(
        select(PipelineStage)
        .options(
            selectinload(PipelineStage.entries)
            .selectinload(PipelineEntry.lead)
        )
        .order_by(PipelineStage.position.asc())
    ).all()

    return PipelineBoardResponse(
        stages=[
            PipelineStageResponse(
                id=stage.id,
                name=stage.name,
                position=stage.position,
                is_active=stage.is_active,
                leads=[
                    PipelineLeadSummary(
                        id=entry.lead.id,
                        name=entry.lead.name,
                        source=entry.lead.source,
                    )
                    for entry in sorted(
                        stage.entries, key=lambda item: item.created_at
                    )
                    if entry.lead is not None
                ],
            )
            for stage in stages
        ]
    )


@router.post("/leads/{lead_id}/move", response_model=PipelineStageResponse)
def move_lead(
    lead_id: int,
    payload: MoveLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PipelineStageResponse:
    lead = db.scalar(select(Lead).where(Lead.id == lead_id))
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado."
        )

    entry = db.scalar(select(PipelineEntry).where(PipelineEntry.lead_id == lead_id))
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead ainda não foi associado ao pipeline.",
        )

    stage = db.scalar(
        select(PipelineStage).where(
            PipelineStage.id == payload.stage_id, PipelineStage.is_active.is_(True)
        )
    )
    if stage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa do pipeline não encontrada.",
        )

    previous_stage = db.scalar(
        select(PipelineStage).where(PipelineStage.id == entry.stage_id)
    )
    entry.stage_id = stage.id
    entry.assigned_to_id = payload.assigned_to_id or entry.assigned_to_id
    entry.next_action_at = payload.next_action_at
    register_audit_log(
        db,
        actor_id=current_user.id,
        entity="pipeline_entry",
        entity_id=entry.id,
        action="moved",
        payload={
            "lead_id": lead_id,
            "from_stage": previous_stage.name if previous_stage else None,
            "to_stage": stage.name,
        },
    )
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(stage)
    return PipelineStageResponse.model_validate(stage)
