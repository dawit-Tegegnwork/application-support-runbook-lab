from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.landing import render_landing
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


@app.get("/", response_class=HTMLResponse)
def landing_page():
    return render_landing(
        "Application Support Runbook Lab",
        "Production-style support portfolio — runbooks plus a working triage board and ticket API.",
        "Synthetic incidents and organizations only. Not employer-confidential processes.",
        "application-support-runbook-lab",
        extra_links=[("/board", "Triage board")],
        quick_steps=[
            'Check <a href="/health">/health</a>',
            'Open <a href="/board">/board</a> — see INC-240601 and other seeded tickets',
            "<code>GET /api/tickets?ticket_number=INC-240601</code>",
            "Run <code>python scripts/data_health_check.py</code> for synthetic SQL-style checks",
        ],
    )


@app.get("/board", response_class=HTMLResponse)
def triage_board():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Support Triage Board</title>
      <style>
        body { font-family: system-ui, sans-serif; margin: 0; background: #FBF7F0; color: #0E2A3B; }
        .banner { background: #ecfdf5; border-bottom: 1px solid #6ee7b7; color: #065f46; padding: 0.65rem 1.5rem; font-size: 0.85rem; }
        main { max-width: 1000px; margin: 0 auto; padding: 1.75rem 1.25rem; }
        .hero { background: #fff; border: 1px solid #F2742C; border-left: 4px solid #F2742C; border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.25rem; }
        .hero strong { color: #F2742C; }
        table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #E8DFD0; border-radius: 12px; overflow: hidden; }
        th, td { padding: 0.75rem 1rem; border-bottom: 1px solid #E8DFD0; text-align: left; font-size: 0.88rem; }
        th { background: #F8F3EA; font-size: 0.72rem; text-transform: uppercase; color: #5B6B73; }
        .p1 { color: #dc2626; font-weight: 700; }
        .p2 { color: #F2742C; font-weight: 700; }
        .p3 { color: #ca8a04; }
        a { color: #0E9E8E; font-weight: 600; }
      </style>
    </head>
    <body>
      <div class="banner"><strong>Synthetic incidents only.</strong> Portfolio demo — not employer-confidential data.</div>
      <main>
        <h1>Support Triage Board</h1>
        <div class="hero" id="hero">Loading featured incident...</div>
        <table>
          <thead><tr><th>Ticket</th><th>Severity</th><th>Status</th><th>Module</th><th>Title</th></tr></thead>
          <tbody id="rows"><tr><td colspan="5">Loading...</td></tr></tbody>
        </table>
        <p style="margin-top:1.25rem"><a href="/">Home</a> · <a href="/docs">API docs</a></p>
      </main>
      <script>
        fetch('/api/tickets').then(r => r.json()).then(tickets => {
          const featured = tickets.find(t => t.ticket_number === 'INC-240601') || tickets[0];
          if (featured) {
            document.getElementById('hero').innerHTML =
              `<strong>${featured.ticket_number}</strong> — ${featured.title}<br><span style="color:#5B6B73;font-size:0.9rem">${featured.description || ''}</span>`;
          }
          document.getElementById('rows').innerHTML = tickets.map(t => {
            const sev = (t.severity || '').toLowerCase();
            const cls = sev === 'p1' ? 'p1' : sev === 'p2' ? 'p2' : sev === 'p3' ? 'p3' : '';
            return `<tr><td>${t.ticket_number}</td><td class="${cls}">${t.severity}</td><td>${t.status}</td><td>${t.module}</td><td>${t.title}</td></tr>`;
          }).join('');
        });
      </script>
    </body>
    </html>
    """


@app.get("/health")
def root_health():
    return {"status": "ok", "service": "application-support-runbook-lab"}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "application-support-runbook-lab"}


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
    ticket_number: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SupportTicket)
    if status:
        query = query.filter(SupportTicket.status == status)
    if severity:
        query = query.filter(SupportTicket.severity == severity)
    if module:
        query = query.filter(SupportTicket.module.ilike(f"%{module}%"))
    if ticket_number:
        query = query.filter(SupportTicket.ticket_number == ticket_number)
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
