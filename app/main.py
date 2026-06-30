from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
def landing_page():
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Application Support Runbook Lab</title>
        <style>
          body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #111827; color: #f9fafb; }
          main { max-width: 1040px; margin: 0 auto; padding: 56px 22px; }
          .hero { border-radius: 30px; padding: 40px; background: linear-gradient(135deg, #1f2937, #111827); border: 1px solid #374151; box-shadow: 0 28px 70px rgba(0,0,0,.28); }
          .kicker { color: #fbbf24; text-transform: uppercase; letter-spacing: .16em; font-size: 12px; font-weight: 800; }
          h1 { margin: 12px 0; font-size: clamp(34px, 6vw, 62px); line-height: .98; letter-spacing: -.05em; }
          p { color: #d1d5db; line-height: 1.7; font-size: 17px; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 24px; }
          .card { border: 1px solid #374151; border-radius: 18px; padding: 18px; background: rgba(17, 24, 39, .78); }
          .card strong { display: block; margin-bottom: 8px; color: #fff; }
          .actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
          a { color: #111827; background: #fbbf24; padding: 12px 16px; border-radius: 999px; text-decoration: none; font-weight: 800; }
          a.secondary { color: #f9fafb; background: transparent; border: 1px solid #4b5563; }
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <div class="kicker">Application support portfolio lab</div>
            <h1>Incident triage, UAT, release checks, SQL diagnostics, and support documentation.</h1>
            <p>
              A practical support-management demo combining seven runbooks with a synthetic FastAPI issue tracker
              for tickets, severity, root cause, resolution, and follow-up actions.
            </p>
            <div class="grid">
              <div class="card"><strong>Runbooks</strong>Incident triage, vendor escalation, UAT, release, and monitoring.</div>
              <div class="card"><strong>Diagnostics</strong>SQL data-quality checks and reproducible support scenarios.</div>
              <div class="card"><strong>Tracker</strong>Synthetic tickets with severity, status, root cause, and resolution.</div>
            </div>
            <div class="actions">
              <a href="/board">Triage board</a>
              <a class="secondary" href="/docs">Open API docs</a>
              <a class="secondary" href="/api/tickets?ticket_number=INC-240601">INC-240601 sample</a>
            </div>
          </section>
        </main>
      </body>
    </html>
    """


@app.get("/board", response_class=HTMLResponse)
def triage_board():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <title>Support Triage Board</title>
      <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; background: #111827; color: #f9fafb; }
        table { width: 100%; border-collapse: collapse; background: #1f2937; }
        th, td { padding: 0.75rem 1rem; border-bottom: 1px solid #374151; text-align: left; font-size: 0.9rem; }
        th { background: #0f172a; }
        .p1 { color: #fca5a5; font-weight: 700; }
        .p2 { color: #fdba74; font-weight: 700; }
        .p3 { color: #fde68a; }
        a { color: #fbbf24; }
      </style>
    </head>
    <body>
      <h1>Support Triage Board</h1>
      <p>Synthetic incidents for portfolio demo.</p>
      <table>
        <thead><tr><th>Ticket</th><th>Severity</th><th>Status</th><th>Module</th><th>Title</th></tr></thead>
        <tbody id="rows"><tr><td colspan="5">Loading...</td></tr></tbody>
      </table>
      <p><a href="/docs">API docs</a> · <a href="/">Home</a></p>
      <script>
        fetch('/api/tickets').then(r => r.json()).then(tickets => {
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
