from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200


def test_list_seeded_tickets():
    with TestClient(app) as client:
        response = client.get("/api/tickets")
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 3
        numbers = {t["ticket_number"] for t in tickets}
        assert "INC-240601" in numbers


def test_create_and_update_ticket():
    ticket_number = f"INC-TEST-{uuid4().hex[:8]}"
    with TestClient(app) as client:
        create = client.post(
            "/api/tickets",
            json={
                "ticket_number": ticket_number,
                "title": "Synthetic test ticket",
                "description": "Created during automated test run for portfolio demo.",
                "severity": "P4",
                "module": "Testing",
                "reported_by": "pytest@example.com",
            },
        )
        assert create.status_code == 201
        ticket_id = create.json()["id"]

        update = client.patch(
            f"/api/tickets/{ticket_id}",
            json={
                "status": "resolved",
                "root_cause": "Test fixture",
                "resolution": "No action required",
                "follow_up": "None",
            },
        )
        assert update.status_code == 200
        assert update.json()["status"] == "resolved"
        assert update.json()["follow_up"] == "None"


def test_filter_tickets_by_status():
    with TestClient(app) as client:
        response = client.get("/api/tickets", params={"status": "resolved"})
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        assert all(t["status"] == "resolved" for t in tickets)


def test_filter_tickets_by_severity():
    with TestClient(app) as client:
        response = client.get("/api/tickets", params={"severity": "P1"})
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        assert all(t["severity"] == "P1" for t in tickets)


def test_filter_tickets_by_ticket_number():
    with TestClient(app) as client:
        response = client.get("/api/tickets", params={"ticket_number": "INC-240601"})
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) == 1
        assert tickets[0]["ticket_number"] == "INC-240601"


def test_duplicate_ticket_number_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/tickets",
            json={
                "ticket_number": "INC-240601",
                "title": "Duplicate attempt",
                "description": "Should fail because INC-240601 is seeded.",
                "severity": "P4",
                "module": "Testing",
                "reported_by": "pytest@example.com",
            },
        )
        assert response.status_code == 409
