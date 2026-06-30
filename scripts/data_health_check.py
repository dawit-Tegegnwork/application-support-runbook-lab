#!/usr/bin/env python3
"""Run synthetic data-quality checks against the support ticket demo database."""

import sys

from app.models import SessionLocal, SupportTicket, TicketStatus


def main() -> int:
    db = SessionLocal()
    try:
        total = db.query(SupportTicket).count()
        open_tickets = (
            db.query(SupportTicket)
            .filter(
                SupportTicket.status.in_(
                    [TicketStatus.NEW, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_VENDOR]
                )
            )
            .count()
        )
        missing_root_cause = (
            db.query(SupportTicket)
            .filter(SupportTicket.status == TicketStatus.RESOLVED, SupportTicket.root_cause.is_(None))
            .count()
        )
        print(f"Total tickets: {total}")
        print(f"Open / in-progress / waiting vendor: {open_tickets}")
        print(f"Resolved without root cause: {missing_root_cause}")
        if missing_root_cause > 0:
            print("WARN: resolved tickets should document root cause")
            return 1
        print("OK: synthetic support data checks passed")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
