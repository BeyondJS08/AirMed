# Database Design

## Entities
- **User**: Patients and professionals.
- **Appointment**: Scheduled consultations.
- **Availability**: Professional working hours.
- **Service**: Types of services offered.
- **Notification**: Reminders sent via WhatsApp/Telegram/Email.

## Schema
Schema files and migrations are managed via SQLAlchemy and Alembic in `backend-airmed/app/models/`.

## Running Migrations
```bash
cd backend-airmed
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```
