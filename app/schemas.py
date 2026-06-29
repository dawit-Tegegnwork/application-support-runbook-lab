from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Severity, TicketStatus


class TicketCreate(BaseModel):
    ticket_number: str = Field(..., min_length=3, max_length=20)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    severity: Severity = Severity.P3
    module: str = Field(..., min_length=2, max_length=100)
    reported_by: str = Field(..., min_length=2, max_length=100)
    assigned_to: str | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: Severity | None = None
    module: str | None = None
    root_cause: str | None = None
    status: TicketStatus | None = None
    resolution: str | None = None
    follow_up: str | None = None
    assigned_to: str | None = None


class TicketRead(TicketCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    root_cause: str | None = None
    status: TicketStatus
    resolution: str | None = None
    follow_up: str | None = None
    created_at: datetime
    updated_at: datetime
