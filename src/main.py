from fastapi import FastAPI

from src.core.config import settings
from src.database import model_registry  # noqa: F401
from src.modules.auth.router import router as auth_router
from src.modules.students.router import router as students_router
from src.modules.meals.router import router as meals_router
from src.modules.users.router import router as users_router
from src.modules.menus.router import router as menus_router
from src.modules.auth.password_reset import router as password_reset_router

from src.modules.dashboard.router import (
    router as dashboard_router,
)
from src.modules.qr_codes.router import router as qr_codes_router
from src.modules.attendance.router import (
    router as attendance_router,
)
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "Hostel Mess Management API is running",
    }


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    students_router,
    prefix="/api/v1",
)

app.include_router(
    meals_router,
    prefix="/api/v1",
)

app.include_router(
    qr_codes_router,
    prefix="/api/v1",
)

app.include_router(
    attendance_router,
    prefix="/api/v1",
)

app.include_router(
    users_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

app.include_router(
    menus_router,
    prefix="/api/v1",
)

app.include_router(password_reset_router, prefix="/api/v1")
