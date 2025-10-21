from __future__ import annotations
import sqlite3

def _one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0]) if row else 0


def count_total_todos(conn: sqlite3.Connection) -> int:
    return _one(conn, "SELECT COUNT(*) FROM todos")


def count_open(conn: sqlite3.Connection) -> int:
    return _one(conn, "SELECT COUNT(*) FROM todos WHERE is_done = 0")


def count_done(conn: sqlite3.Connection) -> int:
    return _one(conn, "SELECT COUNT(*) FROM todos WHERE is_done = 1")


def count_users(conn: sqlite3.Connection) -> int:
    return _one(conn, "SELECT COUNT(*) FROM users")

# Bonus examples you can show students:

def count_overdue(conn: sqlite3.Connection) -> int:
    return _one(conn, "SELECT COUNT(*) FROM todos WHERE is_done = 0 AND due_date IS NOT NULL AND due_date < date('now')")


def count_due_today(conn: sqlite3.Connection) -> int:
    return _one(conn, "SELECT COUNT(*) FROM todos WHERE due_date = date('now')")