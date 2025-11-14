"""Configuration helpers for database connectivity and runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULTS = {
    "DB_HOST": "localhost",
    "DB_USER": "root",
    "DB_PASSWORD": "",  # Must be set via environment variable
    "DB_NAME": "expense_tracker",
}


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection parameters sourced from environment variables."""

    host: str
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration values from environment variables with defaults."""
        values = {
            key: os.getenv(key, default)
            for key, default in DEFAULTS.items()
        }
        return cls(
            host=values["DB_HOST"],
            user=values["DB_USER"],
            password=values["DB_PASSWORD"],
            database=values["DB_NAME"],
        )


