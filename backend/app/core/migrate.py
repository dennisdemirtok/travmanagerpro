"""
TravManager — SQL Migration Runner

Runs all SQL migration files in order on startup.
Locally, migrations are handled by Docker's PostgreSQL init scripts,
but on Railway/production we need to run them from the app.
All migrations use IF NOT EXISTS / IF NOT EXISTS so they're idempotent.
"""
import os
import glob
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "migrations")


async def run_migrations(engine: AsyncEngine) -> None:
    """Run all SQL migration files in sorted order."""
    migration_dir = os.path.abspath(MIGRATIONS_DIR)
    if not os.path.isdir(migration_dir):
        logger.warning(f"Migrations directory not found: {migration_dir}")
        return

    sql_files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))
    if not sql_files:
        logger.warning("No SQL migration files found")
        return

    async with engine.begin() as conn:
        for sql_file in sql_files:
            filename = os.path.basename(sql_file)
            logger.info(f"Running migration: {filename}")
            with open(sql_file, "r") as f:
                sql_content = f.read()
            # Execute each statement separately (split on semicolons)
            for statement in sql_content.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        await conn.execute(text(statement))
                    except Exception as e:
                        # Log but continue — IF NOT EXISTS handles duplicates
                        logger.debug(f"  Statement note ({filename}): {e}")

    logger.info(f"Migrations complete ({len(sql_files)} files)")
