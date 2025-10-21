from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional


@contextmanager
def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()




def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT,
            is_done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_todos_user ON todos(user_id);
        CREATE INDEX IF NOT EXISTS idx_todos_done ON todos(is_done);
        """
        )
    conn.commit()


# ---- Users ----


def create_user(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("INSERT INTO users(name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid




def delete_user(conn: sqlite3.Connection, user_id: int) -> bool:
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0




def list_users(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    return conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()


# ---- Todos ----


def create_todo(conn: sqlite3.Connection, user_id: int, title: str, due_date: Optional[str]) -> int:
    cur = conn.execute(
        "INSERT INTO todos(user_id, title, due_date) VALUES (?, ?, ?)",
        (user_id, title, due_date),
        )
    conn.commit()
    return cur.lastrowid




def update_todo(
    conn: sqlite3.Connection,
    todo_id: int,
    *,
    title: Optional[str] = None,
    due_date: Optional[str] = None,
    is_done: Optional[int] = None,
    ) -> bool:
    fields = []
    params = []
    if title is not None:
        fields.append("title = ?"); params.append(title)
    if due_date is not None:
        fields.append("due_date = ?"); params.append(due_date)
    if is_done is not None:
        fields.append("is_done = ?"); params.append(int(bool(is_done)))
    if not fields:
        return False
    fields.append("updated_at = (strftime('%Y-%m-%dT%H:%M:%S','now'))")
    params.append(todo_id)
    cur = conn.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    return cur.rowcount > 0




def delete_todo(conn: sqlite3.Connection, todo_id: int) -> bool:
    cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    return cur.rowcount > 0




def list_todos(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    sql = (
        '''SELECT t.id, t.title, t.due_date, t.is_done, t.user_id, u.name AS user_name 
        FROM todos t JOIN users u ON u.id = t.user_id 
        ORDER BY COALESCE(t.due_date, '9999-12-31'), t.is_done, t.id
        '''
    )
    return conn.execute(sql).fetchall()