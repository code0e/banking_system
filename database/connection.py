"""SQLite connection, schema initialization, and transaction management."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from database.schema import SCHEMA


class Database:
    """Manage short-lived SQLite connections for one database file."""

    SCHEMA_VERSION = 2

    def __init__(self, path: str | Path = "banking_system.db") -> None:
        self.path = str(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a configured connection and always close it."""
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create missing tables and upgrade the schema to version 2.

        All statements are idempotent, so existing Phase 5 databases retain
        their customer, account, and transaction records during the upgrade.
        """
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION}")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a write transaction with explicit commit or rollback."""
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
