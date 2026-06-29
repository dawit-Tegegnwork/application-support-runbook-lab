from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import SessionLocal, Severity, SupportTicket, TicketStatus, init_db
from app.schemas import TicketCreate, TicketRead, TicketUpdate


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_tickets(db: Session) -> None:
    if db.query(SupportTicket).count() > 0:
        return
    samples = [
        SupportTicket(
            ticket_number="INC-240601",
            title="Enrollment batch stuck in pending state",
            description=(
                "Synthetic incident: 12 enrollment records remain in 'pending' after "
                "nightly batch. Users report missing confirmation emails."
            ),
            severity=Severity.P2,
            module="Enrollment",
            root_cause="Downstream message queue consumer lag",
            status=TicketStatus.RESOLVED,
            resolution="Restarted consumer pod; replayed dead-letter queue messages.",
            follow_up="Monitor queue depth for 72 hours; add alert at depth > 100.",
            reported_by="helpdesk@demo-org.example",
            assigned_to="Alex Kim",
        ),
        SupportTicket(
            ticket_number="INC-240615",
            title="Report export timeout for large date ranges",
            description="Synthetic: PDF export fails when date range exceeds 90 days.",
            severity=Severity.P3,
            module="Reporting",
            status=TicketStatus.IN_PROGRESS,
            reported_by="analyst@demo-org.example",
            assigned_to="Jordan Lee",
        ),
        SupportTicket(
            ticket_number="INC-240620",
            title="Login redirect loop on Safari 17",
            description="Synthetic: Safari users redirected indefinitely after SSO callback.",
            severity=Severity.P1,
            module="Authentication",
            root_cause="Cookie SameSite misconfiguration after CDN update",
            status=TicketStatus.WAITING_VENDOR,
            resolution="Vendor patch scheduled for 2024-06-22 maintenance window.",
            follow_up="Communicate workaround: use Chrome or Firefox until patch deployed.",
            reported_by="security@demo-org.example",
            assigned_to="Taylor Brooks",
        ),
    ]
    db.add_all(samples)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_tickets(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Application Support Issue Tracker (Demo)",
    description="Optional demo app for the Application Support Runbook Lab portfolio project.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/tickets", response_model=TicketRead, status_code=201)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    if db.query(SupportTicket).filter(SupportTicket.ticket_number == payload.ticket_number).first():
        raise HTTPException(status_code=409, detail="Ticket number already exists")
    ticket = SupportTicket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/api/tickets", response_model=list[TicketRead])
def list_tickets(
    status: TicketStatus | None = None,
    severity: Severity | None = None,
    module: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SupportTicket)
    if status:
        query = query.filter(SupportTicket.status == status)
    if severity:
        query = query.filter(SupportTicket.severity == severity)
    if module:
        query = query.filter(SupportTicket.module.ilike(f"%{module}%"))
    return query.order_by(SupportTicket.created_at.desc()).all()


@app.get("/api/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.patch("/api/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, key, value)
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket
