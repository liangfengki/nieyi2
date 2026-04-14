from sqlalchemy.ext.asyncio import AsyncConnection


async def _column_exists(conn: AsyncConnection, table_name: str, column_name: str) -> bool:
    result = await conn.exec_driver_sql(f"PRAGMA table_info({table_name})")
    columns = result.fetchall()
    return any(col[1] == column_name for col in columns)


async def _table_exists(conn: AsyncConnection, table_name: str) -> bool:
    result = await conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    )
    return result.fetchone() is not None


async def _ensure_column(conn: AsyncConnection, table_name: str, column_name: str, definition: str) -> None:
    if not await _column_exists(conn, table_name, column_name):
        await conn.exec_driver_sql(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


async def _ensure_index(conn: AsyncConnection, index_name: str, table_name: str, column_name: str) -> None:
    await conn.exec_driver_sql(
        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})"
    )


async def _ensure_email_login_codes_table(conn: AsyncConnection) -> None:
    if await _table_exists(conn, "email_login_codes"):
        return

    await conn.exec_driver_sql(
        """
        CREATE TABLE email_login_codes (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            last_sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            send_count INTEGER DEFAULT 1,
            verify_attempts INTEGER DEFAULT 0,
            request_ip TEXT,
            consumed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    await conn.exec_driver_sql(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_email_login_codes_email ON email_login_codes (email)"
    )
    await conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_email_login_codes_request_ip ON email_login_codes (request_ip)"
    )


async def apply_startup_migrations(conn: AsyncConnection) -> None:
    dialect = conn.dialect.name
    if dialect != "sqlite":
        return

    await _ensure_email_login_codes_table(conn)
    await _ensure_column(conn, "license_codes", "owner_user_id", "TEXT")
    await _ensure_column(conn, "generation_tasks", "user_id", "TEXT")

    await _ensure_index(conn, "ix_license_codes_owner_user_id", "license_codes", "owner_user_id")
    await _ensure_index(conn, "ix_generation_tasks_user_id", "generation_tasks", "user_id")
