import pytest
from datetime import time, date, datetime, timedelta
from fastapi.testclient import TestClient

from app.models.availability import Availability
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.user import User
from app.core.security import get_password_hash


def _create_professional(db_session, email: str, name: str) -> User:
    user = User(
        email=email,
        full_name=name,
        hashed_password=get_password_hash("password123"),
        is_professional=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_as(client: TestClient, email: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return resp.json()["access_token"]


class TestCreateAvailability:
    def test_create_availability_ok(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["day_of_week"] == 0
        assert data["start_time"] == "09:00:00"
        assert data["end_time"] == "17:00:00"
        assert data["professional_id"] == test_professional.id
        assert data["is_active"] is True

    def test_create_availability_not_professional(self, client, test_user):
        token = _login_as(client, "test@example.com")
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_create_availability_unauthenticated(self, client):
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
        )
        assert resp.status_code == 401

    def test_create_availability_overlap(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "10:00", "end_time": "13:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    def test_create_availability_abutting_is_ok(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "12:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

    def test_create_availability_invalid_day(self, client, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 7, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_create_availability_invalid_day_negative(self, client, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": -1, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_create_availability_end_before_start(self, client, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "17:00", "end_time": "09:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestListAvailability:
    def test_list_availability_owner(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            "/api/v1/availability/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_availability_empty(self, client, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.get(
            "/api/v1/availability/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_availability_other_professional(self, client, db_session, test_professional):
        prof_a_token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {prof_a_token}"},
        )
        prof_b = _create_professional(db_session, "other@example.com", "Dr. Other")
        prof_b_token = _login_as(client, "other@example.com")
        resp = client.get(
            "/api/v1/availability/",
            headers={"Authorization": f"Bearer {prof_b_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestUpdateAvailability:
    def test_update_availability_ok(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        create_resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        av_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/v1/availability/{av_id}",
            json={"start_time": "10:00", "end_time": "16:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["start_time"] == "10:00:00"
        assert data["end_time"] == "16:00:00"

    def test_update_availability_not_owner(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        create_resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        av_id = create_resp.json()["id"]
        prof_b = _create_professional(db_session, "other@example.com", "Dr. Other")
        prof_b_token = _login_as(client, "other@example.com")
        resp = client.put(
            f"/api/v1/availability/{av_id}",
            json={"start_time": "10:00"},
            headers={"Authorization": f"Bearer {prof_b_token}"},
        )
        assert resp.status_code == 403

    def test_update_availability_overlap(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        create_resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "13:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        av_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/v1/availability/{av_id}",
            json={"start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    def test_update_availability_not_found(self, client, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.put(
            "/api/v1/availability/99999",
            json={"start_time": "10:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestDeleteAvailability:
    def test_delete_availability_ok(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        create_resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        av_id = create_resp.json()["id"]
        resp = client.delete(
            f"/api/v1/availability/{av_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    def test_delete_availability_not_owner(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        create_resp = client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        av_id = create_resp.json()["id"]
        prof_b = _create_professional(db_session, "other@example.com", "Dr. Other")
        prof_b_token = _login_as(client, "other@example.com")
        resp = client.delete(
            f"/api/v1/availability/{av_id}",
            headers={"Authorization": f"Bearer {prof_b_token}"},
        )
        assert resp.status_code == 403

    def test_delete_availability_not_found(self, client, test_professional):
        token = _login_as(client, "professional@example.com")
        resp = client.delete(
            "/api/v1/availability/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestAvailableSlots:
    def test_available_slots_basic(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": test_professional.id, "date": "2026-06-29"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["start_time"] == "2026-06-29T09:00:00"
        assert data[0]["end_time"] == "2026-06-29T17:00:00"

    def test_available_slots_with_appointment(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        appointment = Appointment(
            professional_id=test_professional.id,
            patient_id=test_professional.id,
            start_time=datetime(2026, 6, 29, 10, 0, 0),
            end_time=datetime(2026, 6, 29, 11, 0, 0),
            status="scheduled",
        )
        db_session.add(appointment)
        db_session.commit()
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": test_professional.id, "date": "2026-06-29"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["start_time"] == "2026-06-29T09:00:00"
        assert data[0]["end_time"] == "2026-06-29T10:00:00"
        assert data[1]["start_time"] == "2026-06-29T11:00:00"
        assert data[1]["end_time"] == "2026-06-29T17:00:00"

    def test_available_slots_no_window(self, client, test_professional):
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": test_professional.id, "date": "2026-06-29"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_available_slots_with_service_duration(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        service = Service(
            professional_id=test_professional.id,
            name="Checkup",
            duration_minutes=30,
        )
        db_session.add(service)
        db_session.commit()
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={
                "professional_id": test_professional.id,
                "date": "2026-06-29",
                "service_id": service.id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 16
        for i, slot in enumerate(data):
            expected_start = datetime(2026, 6, 29, 9 + i // 2, 30 * (i % 2))
            expected_end = expected_start + timedelta(minutes=30)
            assert slot["start_time"] == expected_start.isoformat()
            assert slot["end_time"] == expected_end.isoformat()

    def test_available_slots_multiple_windows(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "14:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": test_professional.id, "date": "2026-06-29"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["start_time"] == "2026-06-29T09:00:00"
        assert data[0]["end_time"] == "2026-06-29T12:00:00"
        assert data[1]["start_time"] == "2026-06-29T14:00:00"
        assert data[1]["end_time"] == "2026-06-29T17:00:00"

    def test_available_slots_cancelled_appointment(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        appointment = Appointment(
            professional_id=test_professional.id,
            patient_id=test_professional.id,
            start_time=datetime(2026, 6, 29, 10, 0, 0),
            end_time=datetime(2026, 6, 29, 11, 0, 0),
            status="cancelled",
        )
        db_session.add(appointment)
        db_session.commit()
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": test_professional.id, "date": "2026-06-29"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["start_time"] == "2026-06-29T09:00:00"
        assert data[0]["end_time"] == "2026-06-29T17:00:00"

    def test_available_slots_partial_overlap(self, client, db_session, test_professional):
        token = _login_as(client, "professional@example.com")
        client.post(
            "/api/v1/availability/",
            json={"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        appointment = Appointment(
            professional_id=test_professional.id,
            patient_id=test_professional.id,
            start_time=datetime(2026, 6, 29, 8, 0, 0),
            end_time=datetime(2026, 6, 29, 10, 30, 0),
            status="scheduled",
        )
        db_session.add(appointment)
        db_session.commit()
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": test_professional.id, "date": "2026-06-29"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["start_time"] == "2026-06-29T10:30:00"
        assert data[0]["end_time"] == "2026-06-29T17:00:00"

    def test_available_slots_professional_not_found(self, client):
        resp = client.get(
            "/api/v1/availability/available-slots",
            params={"professional_id": 99999, "date": "2026-06-29"},
        )
        assert resp.status_code == 404
