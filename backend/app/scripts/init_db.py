# app/scripts/init_db.py

from sqlalchemy import text

from app.db.session import engine, metadata


def create_schemas() -> None:
    """
    Ensure the core and analytics schemas exist before creating tables.
    """
    print("Creating schemas core & analytics (if not exists)...")
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
    print("Schemas ready.")


def create_tables() -> None:
    """
    Create all tables defined in app.db.tables against the current database.
    """
    # Important: importing tables registers them on the shared `metadata`
    import app.db.tables  # noqa: F401

    create_schemas()

    print("Creating tables from metadata...")
    metadata.create_all(bind=engine)
    print("All tables created (if they did not already exist).")


def main() -> None:
    print("Initializing database…")
    create_tables()
    print("✅ Database initialization complete.")


if __name__ == "__main__":
    main()
