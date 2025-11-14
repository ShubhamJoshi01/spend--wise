"""Database connectivity utilities."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import mysql.connector
from mysql.connector.connection import MySQLConnection

from .config import DatabaseConfig


def get_connection(config: DatabaseConfig | None = None) -> MySQLConnection:
    """Return a new MySQL connection using the provided or environment config."""
    config = config or DatabaseConfig.from_env()
    return mysql.connector.connect(
        host=config.host,
        user=config.user,
        password=config.password,
        database=config.database,
    )


@contextmanager
def db_cursor(
    config: DatabaseConfig | None = None, commit: bool = False
) -> Generator[tuple[MySQLConnection, mysql.connector.cursor.MySQLCursor], None, None]:
    """Yield a managed connection and cursor pair.

    Args:
        config: Optional pre-loaded configuration.
        commit: Whether to commit at exit.
    """
    conn = get_connection(config)
    cursor = conn.cursor()
    try:
        yield conn, cursor
        if commit:
            conn.commit()
    finally:
        cursor.close()
        conn.close()




