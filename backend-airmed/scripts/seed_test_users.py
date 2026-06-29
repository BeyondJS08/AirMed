"""Seed test users for frontend manual testing.

Run from backend-airmed/:
    source .venv/bin/activate && python scripts/seed_test_users.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User


TEST_USERS = [
    {
        "email": "patient@airmed.test",
        "full_name": "Test Patient",
        "password": "Patient123!",
        "is_professional": False,
    },
    {
        "email": "professional@airmed.test",
        "full_name": "Dr. Test Professional",
        "password": "Pro123!",
        "is_professional": True,
    },
]


def seed(db: Session) -> None:
    for spec in TEST_USERS:
        existing = db.query(User).filter(User.email == spec["email"]).first()
        if existing:
            print(f"User already exists: {spec['email']} (id={existing.id})")
            continue

        user = User(
            email=spec["email"],
            full_name=spec["full_name"],
            hashed_password=get_password_hash(spec["password"]),
            is_professional=spec["is_professional"],
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created {('professional' if user.is_professional else 'patient')}: {user.email} (id={user.id})")

    print("\nTest credentials:")
    for spec in TEST_USERS:
        role = "professional" if spec["is_professional"] else "patient"
        print(f"  {role}: {spec['email']} / {spec['password']}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
