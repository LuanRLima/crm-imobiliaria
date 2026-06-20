from datetime import datetime

from pydantic import BaseModel


class PipelineLeadSummary(BaseModel):
    id: int
    name: str
    source: str


class PipelineStageCreate(BaseModel):
    name: str
    position: int
    is_active: bool = True


class PipelineStageResponse(BaseModel):
    id: int
    name: str
    position: int
    is_active: bool
    leads: list[PipelineLeadSummary] = []

    model_config = {"from_attributes": True}


class PipelineBoardResponse(BaseModel):
    stages: list[PipelineStageResponse]


class MoveLeadRequest(BaseModel):
    stage_id: int
    assigned_to_id: int | None = None
    next_action_at: datetime | None = None
