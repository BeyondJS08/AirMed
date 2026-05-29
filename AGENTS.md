# AGENTS.md

## Context
Project: AirMed

Description: AirMed is a comprehensive, intelligent appointment scheduling system for the healthcare sector, designed for professionals in medicine, dentistry, psychology, nutrition, and other related fields. This system is designed to efficiently manage your availability and receive appointments from your patients.

In this project, is contemplated:
- Web App
- Mobile App
- Google Calendar integration
- Integration with messaging services (WhatsApp and Telegram) plus AI to assist with appointment scheduling and users with limited technical experience

## Project stages

Stage 1: System Analysis, Design, and Architecture
-  Gathering functional and non-functional requirements based on healthcare professional and patient profiles.
- Defining the system architecture: FastAPI backend, React/Next.js frontend, React Native mobile app, and on-premises local language model (LLM).
- Designing the relational database (PostgreSQL) to manage users, professionals, appointments, availability, and notifications.
- Designing user interfaces (UI/UX) for patients, professionals, and administrators.
- Defining the authentication flow with Google OAuth 2.0 and the appointment scheduling flow via instant messaging.

Stage 2: Development and Integration of Main Modules
- Developing the backend in FastAPI: REST endpoints for managing users, appointments, availability, and notifications.
- Implementing authentication with Google (OAuth 2.0 / Google Sign-In) on web and mobile.
- Web frontend development with React/Next.js: patient panel, professional panel, and availability calendar.
- Development of the client-only mobile application in React Native: scheduling, appointment viewing, and push notifications.
- Integration with the Google Calendar API: automatic event creation, invitations, and reminders for both the professional and the patient.
- Integration of the on-premise Local Language Model (LLM) for interpreting natural language messages sent via WhatsApp/Telegram.
- Development of the WhatsApp bot (WhatsApp Business API) and Telegram bot: message reception, availability analysis, appointment confirmation, and event creation in Google Calendar.

3: Notifications, Reminders, and Automation
- Implementation of the automatic reminder system: sending confirmation and reminder messages via WhatsApp, Telegram, and email to both the patient and the professional.
- Proactive reminder flow configuration for professionals: the system notifies doctors/dentists/psychologists of their upcoming appointments via messaging, eliminating the need for constant platform checks.
- Support for virtual appointments (video call link included in the event) and in-person appointments (office address included in the Google Calendar event).
- Administration panel for configuring availability, services offered, and handling exceptions (cancellations, rescheduling).

4: Testing, Optimization, and Deployment
- Functional testing of the entire flow: from appointment request (web, mobile, or messaging) to confirmation and registration in Google Calendar.
- Usability testing with users with limited technological experience using WhatsApp/Telegram.
- Security testing: OAuth authentication validation, protection of health data, and access control.
- Optimization of backend performance and response times for the local language model.
- Deployment of the system in a production environment (cloud) and of the LLM model on a local server or edge.

## Final Product
- Web application (React/Next.js) with a patient dashboard and a healthcare professional dashboard, with Google login.
- Mobile application (React Native, client-only) for appointment booking and management from iOS and Android devices.
- REST backend API in FastAPI with OAuth 2.0 authentication, availability management, appointment module, and notification engine.
- Conversational bot for WhatsApp and Telegram that allows users with low digital literacy to schedule appointments using natural language messages.
- Local language model (LLM) integrated into the bot to interpret intents, extract dates/times, and confirm professional availability.
- Full integration with Google Calendar: automatic event creation, reminders, and support for virtual and in-person appointments.
- Proactive reminder system for patients and professionals via WhatsApp, Telegram, and email.

## Technical Stack
- Frontend: React/Next.js
- Backend: FastAPI
- Database: PostgreSQL/Supabase
- Mobile: React Native/Expo
- APIS: Google Calendar, OAuth 2.0, Telegram Bot API y WhatsApp Business API
- LLM on-premise: gemma-4-E4B
- Containerization: Podman
