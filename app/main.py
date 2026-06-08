import os
import asyncio
import logging
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.utils.error_handler import http_exception_handler, generic_exception_handler, validation_exception_handler
from app.database.connection import Base, engine
from app.database.connection import SessionLocal
from app.database.schema_patch import (
    ensure_complaints_columns,
    ensure_payments_columns,
    ensure_visitors_columns,
    ensure_complaints_enhancements,
    ensure_deliveries_columns,
    ensure_timestamp_columns,
    ensure_fk_indexes,
    ensure_admin_audit_logs_table,
    ensure_user_auth_columns,
)
import app.models  # noqa: F401
from app.routes.auth import router as auth_router
from app.routes.admin_auth import router as admin_auth_router
from app.routes.admin_residents import router as admin_residents_router
from app.routes.admin_flats import router as admin_flats_router
from app.routes.admin_complaints import router as admin_complaints_router
from app.routes.admin_payments import router as admin_payments_router
from app.routes.admin_notices import router as admin_notices_router
from app.routes.admin_settings import router as admin_settings_router
from app.routes.admin_dashboard import router as admin_dashboard_router
from app.routes.admin_meetings import router as admin_meetings_router
from app.routes.admin_guards import router as admin_guards_router
from app.routes.guard_visitors import router as guard_visitors_router
from app.routes.guard_deliveries import router as guard_deliveries_router
from app.routes.guard_dashboard import router as guard_dashboard_router
from app.routes.guard_flats import router as guard_flats_router
from app.routes.resident_announcements import router as resident_announcements_router
from app.routes.resident_complaints import router as resident_complaints_router
from app.routes.resident_payments import router as resident_payments_router
from app.routes.resident_profile import router as resident_profile_router
from app.routes.resident_meetings import router as resident_meetings_router
from app.routes.resident_chat import router as resident_chat_router
from app.routes.resident_visitors import router as resident_visitors_router
from app.routes.resident_deliveries import router as resident_deliveries_router
from app.services.reminder_service import run_payment_reminders
from app.utils.runtime_config import validate_runtime_config

app = FastAPI(title="SmartSociety Backend", version="1.0.0")
logger = logging.getLogger(__name__)

validate_runtime_config(logger)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)
    ensure_user_auth_columns()
    ensure_complaints_columns()
    ensure_payments_columns()
    ensure_visitors_columns()
    ensure_deliveries_columns()
    ensure_complaints_enhancements()

if os.getenv("AUTO_PATCH_SCHEMA", "false").lower() == "true":
    ensure_user_auth_columns()
    ensure_payments_columns()
    ensure_timestamp_columns()
    ensure_fk_indexes()
    logger.warning(
        "AUTO_PATCH_SCHEMA is enabled. Prefer running `python -m app.database.migrate` before startup for explicit schema prep."
    )

@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)

app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(admin_residents_router)
app.include_router(admin_flats_router)
app.include_router(admin_complaints_router)
app.include_router(admin_payments_router)
app.include_router(admin_notices_router)
app.include_router(admin_settings_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_meetings_router)
app.include_router(admin_guards_router)
app.include_router(guard_visitors_router)
app.include_router(guard_deliveries_router)
app.include_router(guard_dashboard_router)
app.include_router(guard_flats_router)
app.include_router(resident_announcements_router)
app.include_router(resident_complaints_router)
app.include_router(resident_payments_router)
app.include_router(resident_profile_router)
app.include_router(resident_meetings_router)
app.include_router(resident_chat_router)
app.include_router(resident_visitors_router)
app.include_router(resident_deliveries_router)


async def _reminder_loop(interval_minutes: int) -> None:
    """Background loop to send payment reminders."""
    while True:
        await asyncio.sleep(interval_minutes * 60)
        db = None
        try:
            db = SessionLocal()
            run_payment_reminders(db)
        except Exception:
            logger.exception("Reminder loop failed")
        finally:
            try:
                if db:
                    db.close()
            except Exception:
                pass


def _initialize_startup_schema() -> None:
    """Run non-essential startup schema checks without crashing module import."""
    try:
        ensure_admin_audit_logs_table()
    except RuntimeError:
        logger.exception(
            "Admin audit log initialization failed during startup. "
            "Run `python -m app.database.migrate` after the database is ready."
        )


@app.on_event("startup")
async def start_reminder_scheduler() -> None:
    """Run startup checks and start reminder scheduler if enabled."""
    _initialize_startup_schema()
    enabled = os.getenv("REMINDER_ENABLED", "false").lower() == "true"
    interval = int(os.getenv("REMINDER_INTERVAL_MINUTES", "60"))
    if not enabled:
        logger.info("Reminder scheduler disabled")
        return
    asyncio.create_task(_reminder_loop(interval))
