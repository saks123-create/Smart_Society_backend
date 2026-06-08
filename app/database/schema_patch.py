import logging

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine

logger = logging.getLogger(__name__)


def _column_exists(inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _log_patch_failure(patch_name: str, exc: SQLAlchemyError) -> None:
    """Record migration patch failures so schema drift is visible in logs."""
    logger.warning("Schema patch '%s' did not complete: %s", patch_name, exc)


def ensure_timestamp_columns() -> None:
    """Best-effort patch to add created_at/updated_at on core tables."""
    inspector = inspect(engine)
    core_tables = [
        "users",
        "residents",
        "flats",
        "complaints",
        "payments",
        "visitors",
        "deliveries",
        "notices",
        "meeting_summaries",
        "settings",
    ]
    existing_tables = set(inspector.get_table_names())
    targets = [t for t in core_tables if t in existing_tables]
    if not targets:
        return

    try:
        with engine.begin() as conn:
            for table in targets:
                if not _column_exists(inspector, table, "created_at"):
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} "
                            "ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"
                        )
                    )
                if not _column_exists(inspector, table, "updated_at"):
                    conn.execute(
                        text(
                            f"ALTER TABLE {table} "
                            "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ"
                        )
                    )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_timestamp_columns", exc)
        return


def ensure_user_auth_columns() -> None:
    """Best-effort patch for auth-related user columns."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("users")}
    columns_to_add: list[tuple[str, str]] = []

    if "email_verified" not in existing_cols:
        columns_to_add.append(("email_verified", "BOOLEAN DEFAULT FALSE"))

    if not columns_to_add:
        return

    try:
        with engine.begin() as conn:
            for name, col_type in columns_to_add:
                conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )
            if "email_verified" in existing_cols or any(
                name == "email_verified" for name, _ in columns_to_add
            ):
                conn.execute(
                    text(
                        "UPDATE users SET email_verified = FALSE WHERE email_verified IS NULL"
                    )
                )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_user_auth_columns", exc)
        return


def ensure_fk_indexes() -> None:
    """Best-effort patch to add indexes for common FK columns."""
    inspector = inspect(engine)
    table_columns: dict[str, list[str]] = {
        "residents": ["user_id", "flat_id"],
        "visitors": ["flat_id"],
        "deliveries": ["flat_id"],
        "complaints": ["resident_id"],
        "payments": ["resident_id"],
    }
    existing_tables = set(inspector.get_table_names())

    try:
        with engine.begin() as conn:
            for table, columns in table_columns.items():
                if table not in existing_tables:
                    continue
                for column in columns:
                    index_name = f"ix_{table}_{column}"
                    conn.execute(
                        text(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"
                        )
                    )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_fk_indexes", exc)
        return


def ensure_admin_audit_logs_table() -> None:
    """Ensure admin audit log storage exists before admin mutations run."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        raise RuntimeError("Cannot initialize admin audit logs before users table exists")

    try:
        from app.models.admin_audit_log import AdminAuditLog

        AdminAuditLog.__table__.create(bind=engine, checkfirst=True)
    except SQLAlchemyError as exc:
        raise RuntimeError("Failed to initialize admin audit logs table") from exc


def ensure_complaints_columns() -> None:
    """Best-effort patch for complaint columns used by newer features."""
    inspector = inspect(engine)
    if "complaints" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("complaints")}
    columns_to_add: list[tuple[str, str]] = []

    if "category" not in existing_cols:
        columns_to_add.append(("category", "VARCHAR(100)"))
    if "priority" not in existing_cols:
        columns_to_add.append(("priority", "VARCHAR(50)"))
    if "summary" not in existing_cols:
        columns_to_add.append(("summary", "TEXT"))
    if "image_path" not in existing_cols:
        columns_to_add.append(("image_path", "VARCHAR(2048)"))

    should_expand_image_path = "image_path" in existing_cols and engine.dialect.name == "postgresql"

    if not columns_to_add and not should_expand_image_path:
        return

    try:
        with engine.begin() as conn:
            for name, col_type in columns_to_add:
                conn.execute(
                    text(f"ALTER TABLE complaints ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )
            if should_expand_image_path:
                conn.execute(
                    text("ALTER TABLE complaints ALTER COLUMN image_path TYPE VARCHAR(2048)")
                )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_complaints_columns", exc)
        return


def ensure_payments_columns() -> None:
    """Best-effort patch for payment columns used by Razorpay integration."""
    inspector = inspect(engine)
    if "payments" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("payments")}
    columns_to_add: list[tuple[str, str]] = []

    if "currency" not in existing_cols:
        columns_to_add.append(("currency", "VARCHAR(10)"))
    if "provider" not in existing_cols:
        columns_to_add.append(("provider", "VARCHAR(50)"))
    if "provider_order_id" not in existing_cols:
        columns_to_add.append(("provider_order_id", "VARCHAR(100)"))
    if "provider_payment_id" not in existing_cols:
        columns_to_add.append(("provider_payment_id", "VARCHAR(100)"))
    if "provider_signature" not in existing_cols:
        columns_to_add.append(("provider_signature", "VARCHAR(255)"))
    if "idempotency_key" not in existing_cols:
        columns_to_add.append(("idempotency_key", "VARCHAR(120)"))
    if "receipt" not in existing_cols:
        columns_to_add.append(("receipt", "VARCHAR(120)"))
    if "reminder_stage" not in existing_cols:
        columns_to_add.append(("reminder_stage", "INTEGER"))
    if "updated_at" not in existing_cols:
        columns_to_add.append(("updated_at", "TIMESTAMPTZ"))

    if not columns_to_add:
        return

    try:
        with engine.begin() as conn:
            for name, col_type in columns_to_add:
                conn.execute(
                    text(f"ALTER TABLE payments ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_payments_columns", exc)
        return


def ensure_visitors_columns() -> None:
    """Best-effort patch for visitor QR and status fields."""
    inspector = inspect(engine)
    if "visitors" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("visitors")}
    columns_to_add: list[tuple[str, str]] = []

    if "qr_token" not in existing_cols:
        columns_to_add.append(("qr_token", "VARCHAR(120)"))
    if "status" not in existing_cols:
        columns_to_add.append(("status", "VARCHAR(50)"))
    if "pre_registered_at" not in existing_cols:
        columns_to_add.append(("pre_registered_at", "TIMESTAMPTZ"))
    if "valid_until" not in existing_cols:
        columns_to_add.append(("valid_until", "TIMESTAMPTZ"))

    if not columns_to_add:
        return

    try:
        with engine.begin() as conn:
            for name, col_type in columns_to_add:
                conn.execute(
                    text(f"ALTER TABLE visitors ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )
            # Ensure default and backfill for pre_registered_at if possible.
            if "pre_registered_at" in existing_cols or any(
                name == "pre_registered_at" for name, _ in columns_to_add
            ):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE visitors ALTER COLUMN pre_registered_at SET DEFAULT NOW()"
                        )
                    )
                    conn.execute(
                        text(
                            "UPDATE visitors "
                            "SET pre_registered_at = COALESCE(pre_registered_at, created_at, NOW()) "
                            "WHERE pre_registered_at IS NULL"
                        )
                    )
                except SQLAlchemyError as exc:
                    _log_patch_failure("ensure_visitors_columns.backfill", exc)
                    # Some DBs (e.g., SQLite) won't support ALTER COLUMN.
                    pass
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_visitors_columns", exc)
        return


def ensure_deliveries_columns() -> None:
    """Best-effort patch for delivery confirmation fields."""
    inspector = inspect(engine)
    if "deliveries" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("deliveries")}
    columns_to_add: list[tuple[str, str]] = []

    if "resident_confirmed_at" not in existing_cols:
        columns_to_add.append(("resident_confirmed_at", "TIMESTAMPTZ"))
    if "entry_allowed_at" not in existing_cols:
        columns_to_add.append(("entry_allowed_at", "TIMESTAMPTZ"))
    if "delivery_person_name" not in existing_cols:
        columns_to_add.append(("delivery_person_name", "VARCHAR(255)"))
    if "block_tower" not in existing_cols:
        columns_to_add.append(("block_tower", "VARCHAR(100)"))
    if "mobile_number" not in existing_cols:
        columns_to_add.append(("mobile_number", "VARCHAR(20)"))
    if "delivery_type" not in existing_cols:
        columns_to_add.append(("delivery_type", "VARCHAR(50)"))

    if not columns_to_add:
        return

    try:
        with engine.begin() as conn:
            for name, col_type in columns_to_add:
                conn.execute(
                    text(f"ALTER TABLE deliveries ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_deliveries_columns", exc)
        return


def ensure_complaints_enhancements() -> None:
    """Best-effort patch for complaint enhancements (rating + resolution metadata)."""
    inspector = inspect(engine)
    if "complaints" not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns("complaints")}
    columns_to_add: list[tuple[str, str]] = []

    if "rating" not in existing_cols:
        columns_to_add.append(("rating", "INTEGER"))
    if "rating_feedback" not in existing_cols:
        columns_to_add.append(("rating_feedback", "TEXT"))
    if "resolved_at" not in existing_cols:
        columns_to_add.append(("resolved_at", "TIMESTAMPTZ"))

    if not columns_to_add:
        return

    try:
        with engine.begin() as conn:
            for name, col_type in columns_to_add:
                conn.execute(
                    text(f"ALTER TABLE complaints ADD COLUMN IF NOT EXISTS {name} {col_type}")
                )
    except SQLAlchemyError as exc:
        _log_patch_failure("ensure_complaints_enhancements", exc)
        return
