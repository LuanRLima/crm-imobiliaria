from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class LeadCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    source: str
    notes: str | None = None
    broker_id: int | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value and "@" not in value:
            raise ValueError("Informe um e-mail válido.")
        return value.lower() if value else value

    @model_validator(mode="after")
    def validate_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Informe ao menos e-mail ou telefone para o lead.")
        return self


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    status: str | None = None
    notes: str | None = None
    broker_id: int | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value and "@" not in value:
            raise ValueError("Informe um e-mail válido.")
        return value.lower() if value else value


class LeadResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    source: str
    status: str
    notes: str | None = None
    broker_id: int | None = None
    current_stage: str | None = None
    created_at: datetime
    updated_at: datetime
