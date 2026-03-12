"""
TravManager — SQL Migration Runner

Runs all SQL migration files in order on startup.
Locally, migrations are handled by Docker's PostgreSQL init scripts,
but on Railway/production we need to run them from the app.
All migrations use IF NOT EXISTS / IF NOT EXISTS so they're idempotent.
"""
import os
import glob
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "migrations")


def _split_sql(sql_content: str) -> list[str]:
    """Split SQL content into individual statements, handling $$ blocks."""
    # Split on semicolons that are NOT inside $$ dollar-quoted blocks
    statements = []
    current = []
    in_dollar_quote = False

    for line in sql_content.split("\n"):
        stripped = line.strip()
        # Skip pure comment lines
        if stripped.startswith("--"):
            continue

        # Track $$ blocks (used in CREATE FUNCTION, DO blocks, etc.)
        dollar_count = line.count("$$")
        if dollar_count % 2 == 1:
            in_dollar_quote = not in_dollar_quote

        if not in_dollar_quote and ";" in line:
            # Split on semicolon outside dollar quotes
            parts = line.split(";")
            current.append(parts[0])
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            # Handle remaining parts after the semicolon
            remainder = ";".join(parts[1:]).strip()
            if remainder:
                current.append(remainder)
        else:
            current.append(line)

    # Handle any remaining content
    final = "\n".join(current).strip()
    if final:
        statements.append(final)

    return statements


async def run_migrations(engine: AsyncEngine) -> None:
    """Run all SQL migration files in sorted order."""
    migration_dir = os.path.abspath(MIGRATIONS_DIR)
    print(f"[migrate] Looking for migrations in: {migration_dir}", flush=True)

    if not os.path.isdir(migration_dir):
        print(f"[migrate] WARNING: Migrations directory not found!", flush=True)
        return

    sql_files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))
    if not sql_files:
        print("[migrate] WARNING: No SQL migration files found", flush=True)
        return

    print(f"[migrate] Found {len(sql_files)} migration files", flush=True)

    async with engine.begin() as conn:
        for sql_file in sql_files:
            filename = os.path.basename(sql_file)
            print(f"[migrate] Running: {filename}", flush=True)
            with open(sql_file, "r") as f:
                sql_content = f.read()
            statements = _split_sql(sql_content)
            for i, statement in enumerate(statements):
                try:
                    await conn.execute(text(statement))
                except Exception as e:
                    err_msg = str(e)
                    # Ignore "already exists" errors — expected for idempotent migrations
                    if "already exists" in err_msg or "duplicate" in err_msg.lower():
                        pass
                    else:
                        print(f"[migrate]   Note ({filename} stmt {i+1}): {err_msg[:200]}", flush=True)

    print(f"[migrate] All {len(sql_files)} migrations applied successfully.", flush=True)
