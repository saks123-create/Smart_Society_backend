from app.database.schema_patch import (
    ensure_admin_audit_logs_table,
    ensure_complaints_columns,
    ensure_complaints_enhancements,
    ensure_deliveries_columns,
    ensure_fk_indexes,
    ensure_payments_columns,
    ensure_timestamp_columns,
    ensure_user_auth_columns,
    ensure_visitors_columns,
)


def run_migrations() -> None:
    """Apply the project's lightweight schema compatibility patches explicitly."""
    ensure_user_auth_columns()
    ensure_complaints_columns()
    ensure_payments_columns()
    ensure_visitors_columns()
    ensure_deliveries_columns()
    ensure_complaints_enhancements()
    ensure_timestamp_columns()
    ensure_fk_indexes()
    ensure_admin_audit_logs_table()


if __name__ == "__main__":
    run_migrations()
    print("Schema patches applied.")
