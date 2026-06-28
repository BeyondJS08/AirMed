import pytest
from datetime import datetime, time, timedelta, timezone

from app.models.availability import Availability
from app.models.appointment import Appointment
from app.models.user import User
from app.core.security import get_password_hash

FUTURE = datetime(2027, 7, 1, 9, 0, 0, tzinfo=timezone.utc)
FUTURE_DAY = 3  # 2027-07-01 is Thursday


def _create_availability(db_session, professional_id: int):
    av = Availability(
        professional_id=professional_id,
        day_of_week=FUTURE_DAY,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True,
    )
    db_session.add(av)
    db_session.commit()


class TestCreateAppointment:
    def test_book_appointment_ok(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["professional_id"] == test_professional.id
        assert data["status"] == "scheduled"

    def test_book_appointment_no_availability(self, client, test_professional, user_token):
        resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_book_appointment_clash(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409

    def test_book_appointment_past(self, client, test_professional, user_token):
        resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": "2020-01-01T09:00:00Z",
                "end_time": "2020-01-01T10:00:00Z",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_book_appointment_end_before_start(self, client, test_professional, user_token):
        resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": (FUTURE + timedelta(hours=2)).isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_book_appointment_unauthenticated(self, client):
        resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": 1,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
        )
        assert resp.status_code == 401


class TestListAppointments:
    def test_list_as_patient(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_as_professional(self, client, db_session, test_professional, user_token, professional_token):
        _create_availability(db_session, test_professional.id)
        client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            "/api/v1/appointments/",
            headers={"Authorization": f"Bearer {professional_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_filter_status(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            "/api/v1/appointments/?status=cancelled",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_unauthenticated(self, client):
        resp = client.get("/api/v1/appointments/")
        assert resp.status_code == 401


class TestGetAppointment:
    def test_get_by_id(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        resp = client.get(
            f"/api/v1/appointments/{appt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == appt_id

    def test_get_not_found(self, client, user_token):
        resp = client.get(
            "/api/v1/appointments/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    def test_get_not_owner(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        other = User(
            email="other@example.com",
            full_name="Other User",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other)
        db_session.commit()
        other_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "other@example.com", "password": "password123"},
        )
        other_token = other_resp.json()["access_token"]
        resp = client.get(
            f"/api/v1/appointments/{appt_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403


class TestUpdateAppointment:
    def test_cancel_as_patient(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        resp = client.delete(
            f"/api/v1/appointments/{appt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    def test_cancel_as_professional(self, client, db_session, test_professional, user_token, professional_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        resp = client.delete(
            f"/api/v1/appointments/{appt_id}",
            headers={"Authorization": f"Bearer {professional_token}"},
        )
        assert resp.status_code == 204

    def test_cancel_unrelated_user(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        other = User(
            email="other@example.com",
            full_name="Other User",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other)
        db_session.commit()
        other_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "other@example.com", "password": "password123"},
        )
        other_token = other_resp.json()["access_token"]
        resp = client.delete(
            f"/api/v1/appointments/{appt_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403

    def test_cancel_already_cancelled(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        client.delete(f"/api/v1/appointments/{appt_id}", headers={"Authorization": f"Bearer {user_token}"})
        resp = client.delete(
            f"/api/v1/appointments/{appt_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_confirm_as_patient_forbidden(self, client, db_session, test_professional, user_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/appointments/{appt_id}",
            json={"status": "confirmed"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_confirm_as_professional(self, client, db_session, test_professional, user_token, professional_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/appointments/{appt_id}",
            json={"status": "confirmed"},
            headers={"Authorization": f"Bearer {professional_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_complete_as_professional(self, client, db_session, test_professional, user_token, professional_token):
        _create_availability(db_session, test_professional.id)
        create_resp = client.post(
            "/api/v1/appointments/",
            json={
                "professional_id": test_professional.id,
                "start_time": FUTURE.isoformat(),
                "end_time": (FUTURE + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        appt_id = create_resp.json()["id"]
        client.patch(
            f"/api/v1/appointments/{appt_id}",
            json={"status": "confirmed"},
            headers={"Authorization": f"Bearer {professional_token}"},
        )
        resp = client.patch(
            f"/api/v1/appointments/{appt_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {professional_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
