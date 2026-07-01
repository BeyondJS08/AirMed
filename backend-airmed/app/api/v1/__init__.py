from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, services, appointments, availability, notifications, integrations, bots

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(bots.router)
