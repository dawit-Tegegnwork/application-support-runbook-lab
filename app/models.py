import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = "sqlite:///./support_tickets.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Severity(str, enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TicketStatus(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    WAITING_VENDOR = "waiting_vendor"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.P3)
    module: Mapped[str] = mapped_column(String(100))
    root_cause: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.NEW)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str] = mapped_column(String(100))
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
