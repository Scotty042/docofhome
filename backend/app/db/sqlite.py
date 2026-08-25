import sqlite3
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def enforce_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
    """Enable SQLite foreign-key constraints for every application connection."""

    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()
