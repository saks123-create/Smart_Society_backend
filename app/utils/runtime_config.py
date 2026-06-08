import logging
import os

from app.services.notification_service import is_brevo_configured


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() == "true"


def _app_env() -> str:
    return os.getenv("APP_ENV", os.getenv("ENV", "development")).strip().lower()


def is_local_env() -> bool:
    return _app_env() in {"development", "dev", "local", "test"}


def validate_runtime_config(logger: logging.Logger) -> None:
    secret_key = os.getenv("SECRET_KEY", "").strip()
    if not secret_key:
        raise RuntimeError("SECRET_KEY is required.")

    weak_secrets = {
        "replace_with_a_long_random_secret",
        "smartsociety-dev-secret-key-change-me",
        "changeme",
        "secret",
    }
    if len(secret_key) < 32 or secret_key in weak_secrets:
        if is_local_env():
            logger.warning(
                "Using a weak SECRET_KEY in a local environment. Rotate it before sharing or deploying."
            )
        else:
            raise RuntimeError("SECRET_KEY must be a strong value outside local development.")

    if not is_local_env():
        if _env_flag("AUTO_CREATE_TABLES"):
            raise RuntimeError("AUTO_CREATE_TABLES must stay disabled outside local development.")
        if _env_flag("AUTO_PATCH_SCHEMA"):
            logger.warning(
                "AUTO_PATCH_SCHEMA is enabled outside local development. Prefer running the migration script explicitly."
            )

    razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    if razorpay_key_id.startswith("rzp_test_") and not is_local_env():
        logger.warning("Razorpay test key detected outside local development.")

    origins = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not origins:
        logger.warning("ALLOWED_ORIGINS is not set. Falling back to localhost only.")

    if is_local_env() and not is_brevo_configured():
        logger.warning(
            "Brevo email is not configured for local development. Forgot-password emails and other notifications will be skipped until BREVO_API_KEY and BREVO_SENDER_EMAIL are set."
        )
        if not _env_flag("RETURN_RESET_TOKEN"):
            logger.warning(
                "RETURN_RESET_TOKEN is disabled, so local forgot-password flows will not expose a reset link fallback."
            )
