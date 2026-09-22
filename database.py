"""SQLite database access for the Campus MakerSpace Checkout System.

This module owns:
- opening the SQLite connection;
- creating the schema;
- executing parameterized SQL;
- converting database rows into useful Python data.

Business rules should live primarily in services.py rather than here.
"""

from pathlib import Path
import sqlite3
from typing import Any, Optional, Sequence


DEFAULT_DB_PATH = Path("data/makerspace.db")
SCHEMA_PATH = Path("schema.sql")


class Database:
    """Manage the application's SQLite connection and database operations."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        """Create a database manager.

        This function creates a database manager using the provided database path.
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()

    def initialize_schema(self) -> None:
        """Create required database tables and constraints.

        This function reads the schema.sql file and executes the schema.
        """
        with open(SCHEMA_PATH, "r") as f:
            schema = f.read()
        self.conn.executescript(schema)

    def execute(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> sqlite3.Cursor:
        """Execute one parameterized SQL statement.

        This function executes a parameterized SQL statement and returns the cursor.
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, parameters)
        self.conn.commit()
        return cursor

    def fetch_one(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> Optional[sqlite3.Row]:
        """Return one database row or None.

        This function executes a parameterized SQL query and returns the first row.
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, parameters)
        data = cursor.fetchone()
        return data

    def fetch_all(
        self,
        sql: str,
        parameters: Sequence[Any] = (),
    ) -> list[sqlite3.Row]:
        """Return all rows from a query.

        This function executes a parameterized SQL query and returns all rows.
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, parameters)
        datas = cursor.fetchall()
        return datas

    def close(self) -> None:
        """Close the SQLite connection.

        This function closes the SQLite connection.
        """
        self.conn.close()
