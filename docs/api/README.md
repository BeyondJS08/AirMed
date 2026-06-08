# API Documentation

## Authentication
- OAuth 2.0 with Google Sign-In.
- JWT tokens for session management.

## Endpoints
- `POST /auth/login` - Login with email/password.
- `POST /auth/register` - Register new user.
- `GET /users/me` - Get current user profile.
- `POST /appointments/` - Create a new appointment.
- `GET /appointments/` - List appointments.
- `PUT /appointments/{id}` - Update appointment.
- `DELETE /appointments/{id}` - Cancel appointment.
- `GET /availability/` - Get professional availability.
- `POST /availability/` - Set availability.

## API Client
Base URL: `http://localhost:8000`
