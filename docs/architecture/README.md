# System Architecture

## Overview
AirMed uses a modular architecture with the following components:
- **Backend**: FastAPI (Python) providing REST API.
- **Frontend**: Next.js (React/TypeScript) for web dashboard.
- **Mobile**: React Native (Expo) for iOS/Android.
- **Database**: PostgreSQL for relational data.
- **Cache/Queue**: Redis for background tasks and caching.
- **Integrations**: Google Calendar API, WhatsApp Business API, Telegram Bot API.
- **LLM**: On-premise Gemma-4-E2B for natural language processing.

## Stages
1. **System Analysis, Design, and Architecture** - Requirements, DB design, UI/UX, Auth flow.
2. **Development and Integration** - Core modules, Google Calendar, LLM, Bots.
3. **Notifications and Automation** - Reminders, virtual/in-person appointments, admin panel.
4. **Testing and Deployment** - Functional, usability, security testing, optimization, cloud deployment.
