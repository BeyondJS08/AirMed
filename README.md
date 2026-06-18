# AirMed
AirMed (Citas Inteligentes)
Es un sistema integral de agendamiento inteligente de citas para el área de la salud, dirigido para profesionales de medicina, odontología, psicología, nutriólogos, entre otros.
Este sistema está diseñado para gestionar su disponibilidad y recibir citas de sus pacientes de forma eficiente.
### AirMed proporciona a los usuarios:
  - Web App
  - Mobile App
  - Integración con Google Calendar
  - Integración con servicios de mensajería (WhatsApp y Telegram) sumado con IA para asistir a usuarios con poca experiencia tecnológica
---
### Estructura del Proyecto
```
AirMed/
├── .github/workflows/    # CI/CD pipelines
├── backend-airmed/       # FastAPI REST API
│   ├── app/              # Application code
│   │   ├── api/v1/       # API routers
│   │   ├── core/         # Config, security
│   │   ├── db/           # SQLAlchemy base & session
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   ├── tests/            # Pytest suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend-airmed/      # Next.js web app
│   ├── app/              # Next.js App Router
│   ├── components/       # React components (shadcn/ui)
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities & API client
│   ├── services/         # Domain services
│   ├── types/            # TypeScript types
│   ├── features/         # Feature modules
│   ├── stores/           # State stores
│   └── tests/            # Test suite
├── mobile-airmed/        # React Native (Expo) app
│   ├── app/              # File-based routing
│   ├── components/       # React components
│   ├── constants/        # App constants
│   ├── hooks/            # Custom hooks
│   ├── api/              # API client
│   ├── services/         # Domain services
│   ├── types/            # TypeScript types
│   ├── features/         # Feature modules
│   └── tests/            # Test suite
├── docs/                 # Architecture & design docs
├── docker-compose.yml    # Local orchestration
└── README.md
```
### Tech Stack
- **Frontend**: React/Next.js + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL
- **Mobile**: React Native/Expo
- **APIs**: Google Calendar, OAuth 2.0, Telegram Bot API, WhatsApp Business API
- **LLM on-premise**: Gemma-4-E2B
- **Containerized**: Docker / Podman
- **CI/CD**: GitHub Actions
### Estructura del Proyecto:
- Frontend: React/Next.js
- Backend: FastAPI
- Database: PostgreSQL/Supabase
- Mobile: React Native/Expo
- API's: Google Calendar, OAuth 2.0, Telegram Bot API y WhatsApp Business API
- LLM on-premise: gemma-4-E4B
- Containerization: Podman
