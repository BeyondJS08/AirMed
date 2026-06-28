from datetime import datetime, timezone
import time

from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.appointment import Appointment
from app.models.user import User
from app.core.security import get_password_hash
from app.services.notification_service import (
    create_notification,
    get_notification,
    list_notifications,
    mark_failed,
    mark_read,
    mark_sent,
    notify_appointment_status,
)


def test_create_notification(db_session, test_user):
    n = create_notification(db_session, user_id=test_user.id, channel=NotificationChannel.email, subject="Test", message="Hello")
    assert n.user_id == test_user.id
    assert n.channel == NotificationChannel.email
    assert n.status == NotificationStatus.pending
    assert n.subject == "Test"
    assert n.message == "Hello"
    assert n.appointment_id is None
    assert n.created_at is not None


def test_create_notification_with_appointment(db_session, test_user):
    patient = test_user
    pro = User(email="pro@t.com", full_name="Pro", hashed_password=get_password_hash("p"), is_professional=True, is_active=True)
    db_session.add(pro)
    db_session.commit()
    appt = Appointment(professional_id=pro.id, patient_id=patient.id, start_time=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), end_time=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc), status="scheduled")
    db_session.add(appt)
    db_session.commit()
    n = create_notification(db_session, user_id=patient.id, message="With appt", appointment_id=appt.id)
    assert n.appointment_id == appt.id


def test_list_notifications(db_session, test_user):
    u = test_user
    for i in range(3):
        create_notification(db_session, user_id=u.id, message=f"msg{i}")
    notifs = list_notifications(db_session, u.id)
    assert len(notifs) == 3


def test_list_notifications_filter_status(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="pending")
    mark_sent(db_session, n.id)
    pending = list_notifications(db_session, u.id, status=NotificationStatus.pending)
    assert len(pending) == 0
    sent = list_notifications(db_session, u.id, status=NotificationStatus.sent)
    assert len(sent) == 1


def test_list_notifications_scoped(db_session, test_user):
    u1 = test_user
    u2 = User(email="other@t.com", full_name="Other", hashed_password=get_password_hash("p"), is_active=True)
    db_session.add(u2)
    db_session.commit()
    create_notification(db_session, user_id=u1.id, message="mine")
    create_notification(db_session, user_id=u2.id, message="not mine")
    notifs = list_notifications(db_session, u1.id)
    assert len(notifs) == 1


def test_list_notifications_ordered(db_session, test_user):
    u = test_user
    create_notification(db_session, user_id=u.id, message="first")
    time.sleep(0.01)
    create_notification(db_session, user_id=u.id, message="second")
    notifs = list_notifications(db_session, u.id)
    assert notifs[0].message == "second"


def test_get_notification(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="findme")
    found = get_notification(db_session, n.id)
    assert found is not None
    assert found.id == n.id


def test_get_notification_not_found(db_session):
    assert get_notification(db_session, 9999) is None


def test_mark_sent(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="x")
    updated = mark_sent(db_session, n.id)
    assert updated.status == NotificationStatus.sent
    assert updated.sent_at is not None


def test_mark_failed(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="x")
    updated = mark_failed(db_session, n.id, "SMTP error")
    assert updated.status == NotificationStatus.failed
    assert updated.error == "SMTP error"


def test_mark_read(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="x")
    updated = mark_read(db_session, n.id)
    assert updated.read_at is not None


def test_mark_sent_nonexistent(db_session):
    result = mark_sent(db_session, 9999)
    assert result is None


def test_mark_failed_nonexistent(db_session):
    result = mark_failed(db_session, 9999, "error")
    assert result is None


def test_mark_read_nonexistent(db_session):
    result = mark_read(db_session, 9999)
    assert result is None


def test_hook_on_scheduled_creates_two(db_session):
    patient = User(email="pat_hook@t.com", full_name="Patient", hashed_password=get_password_hash("p"), is_professional=False, is_active=True)
    pro = User(email="pro_hook@t.com", full_name="Pro", hashed_password=get_password_hash("p"), is_professional=True, is_active=True)
    db_session.add_all([patient, pro])
    db_session.commit()
    appt = Appointment(professional_id=pro.id, patient_id=patient.id, start_time=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), end_time=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc), status="scheduled")
    db_session.add(appt)
    db_session.commit()
    notifs = notify_appointment_status(db_session, appt)
    assert len(notifs) == 2
    assert {n.user_id for n in notifs} == {patient.id, pro.id}
    assert all(n.status == NotificationStatus.pending for n in notifs)
    assert all(n.appointment_id == appt.id for n in notifs)
    assert all(n.subject == "Appointment Booked" for n in notifs)


def test_hook_on_cancelled_uses_cancel_subject(db_session):
    patient = User(email="pat_cancel@t.com", full_name="Patient", hashed_password=get_password_hash("p"), is_professional=False, is_active=True)
    pro = User(email="pro_cancel@t.com", full_name="Pro", hashed_password=get_password_hash("p"), is_professional=True, is_active=True)
    db_session.add_all([patient, pro])
    db_session.commit()
    appt = Appointment(professional_id=pro.id, patient_id=patient.id, start_time=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), end_time=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc), status="cancelled")
    db_session.add(appt)
    db_session.commit()
    notifs = notify_appointment_status(db_session, appt)
    assert len(notifs) == 2
    assert all(n.subject == "Appointment Cancelled" for n in notifs)


def test_hook_on_confirmed_uses_confirm_subject(db_session):
    patient = User(email="pat_conf@t.com", full_name="Patient", hashed_password=get_password_hash("p"), is_professional=False, is_active=True)
    pro = User(email="pro_conf@t.com", full_name="Pro", hashed_password=get_password_hash("p"), is_professional=True, is_active=True)
    db_session.add_all([patient, pro])
    db_session.commit()
    appt = Appointment(professional_id=pro.id, patient_id=patient.id, start_time=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), end_time=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc), status="confirmed")
    db_session.add(appt)
    db_session.commit()
    notifs = notify_appointment_status(db_session, appt)
    assert all(n.subject == "Appointment Confirmed" for n in notifs)


def test_list_notifications_api(client, user_token, db_session, test_user):
    create_notification(db_session, user_id=test_user.id, message="hello")
    resp = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["message"] == "hello"


def test_list_notifications_api_unauthenticated(client):
    resp = client.get("/api/v1/notifications/")
    assert resp.status_code == 401


def test_get_notification_api(client, user_token, db_session, test_user):
    n = create_notification(db_session, user_id=test_user.id, message="getme")
    resp = client.get(f"/api/v1/notifications/{n.id}", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "getme"


def test_get_notification_api_not_found(client, user_token):
    resp = client.get("/api/v1/notifications/9999", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 404


def test_get_notification_api_forbidden(client, user_token, db_session):
    other = User(email="other2@t.com", full_name="Other", hashed_password=get_password_hash("p"), is_active=True)
    db_session.add(other)
    db_session.commit()
    n = create_notification(db_session, user_id=other.id, message="secret")
    resp = client.get(f"/api/v1/notifications/{n.id}", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_mark_read_api(client, user_token, db_session, test_user):
    n = create_notification(db_session, user_id=test_user.id, message="readme")
    resp = client.put(f"/api/v1/notifications/{n.id}/read", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


def test_mark_read_api_not_found(client, user_token):
    resp = client.put("/api/v1/notifications/9999/read", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 404


def test_mark_read_api_forbidden(client, user_token, db_session):
    other = User(email="other3@t.com", full_name="Other", hashed_password=get_password_hash("p"), is_active=True)
    db_session.add(other)
    db_session.commit()
    n = create_notification(db_session, user_id=other.id, message="notmine")
    resp = client.put(f"/api/v1/notifications/{n.id}/read", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403
