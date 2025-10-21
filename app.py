from __future__ import annotations

from __future__ import annotations
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

import db_functions as db
import aggregates as agg

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "todo.db"

app = Flask(__name__)

# Initialize schema
with db.get_conn(DB_PATH) as conn:
    db.init_db(conn)


@app.get("/")
def index():
    with db.get_conn(DB_PATH) as conn:
        users = db.list_users(conn)
        todos = db.list_todos(conn)
        counts = {
            "total": agg.count_total_todos(conn),
            "open": agg.count_open(conn),
            "done": agg.count_done(conn),
            "users": agg.count_users(conn),
        }
    return render_template("index.html", users=users, todos=todos, counts=counts)


# ---- Users ----
@app.post("/users_add")
def users_add():
    name = request.form.get("name", "").strip()
    if name:
        with db.get_conn(DB_PATH) as conn:
            db.create_user(conn, name)
    return redirect(url_for("index"))


@app.post("/users/delete/<int:user_id>")
def users_delete(user_id: int):
    with db.get_conn(DB_PATH) as conn:
        db.delete_user(conn, user_id)
    return redirect(url_for("index"))


# ---- Todos ----
@app.post("/todos/add")
def todos_add():
    title = request.form.get("title", "").strip()
    due = request.form.get("due_date") or None
    user_id = request.form.get("user_id")
    if title and user_id:
        with db.get_conn(DB_PATH) as conn:
            db.create_todo(conn, int(user_id), title, due)
    return redirect(url_for("index"))


@app.post("/todos/delete/<int:todo_id>")
def todos_delete(todo_id: int):
    with db.get_conn(DB_PATH) as conn:
        db.delete_todo(conn, todo_id)
    return redirect(url_for("index"))


@app.post("/todos/edit/<int:todo_id>")
def todos_edit(todo_id: int):
    title = request.form.get("title")
    due = request.form.get("due_date") or None
    is_done = 1 if request.form.get("is_done") == "on" else 0
    with db.get_conn(DB_PATH) as conn:
        db.update_todo(conn, todo_id, title=title, due_date=due, is_done=is_done)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "todo.db"
SQL_DIR = APP_DIR / "sql"

app = Flask(__name__)

# --- Helper: load named SQL statements from a .sql file ---
def load_sql_map(path: Path) -> dict[str, str]:
    """Parses -- name: <key> blocks into a dict of {key: sql}."""
    text = path.read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    current = None
    lines = []
    for line in text.splitlines():
        if line.strip().lower().startswith("-- name:"):
            if current and lines:
                blocks[current] = "".join(lines).strip().rstrip(";")
                lines = []
            current = line.split(":", 1)[1].strip()
        else:
            lines.append(line)
    if current and lines:
        blocks[current] = "".join(lines).strip().rstrip(";")
    return blocks

FUN = load_sql_map(SQL_DIR / "functions.sql")
AGG = load_sql_map(SQL_DIR / "aggregates.sql")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure schema exists at startup
with get_db() as conn:
    conn.executescript(FUN["schema"])
    conn.commit()


@app.get("/")
def index():
    with get_db() as conn:
        todos = conn.execute(FUN["list_all"]).fetchall()
        counts = {
            "total": conn.execute(AGG["count_total"]).fetchone()[0],
            "open": conn.execute(AGG["count_open"]).fetchone()[0],
            "done": conn.execute(AGG["count_done"]).fetchone()[0],
        }
    return render_template("index.html", todos=todos, counts=counts)


@app.post("/add")
def add():
    title = request.form.get("title", "").strip()
    due = request.form.get("due_date") or None
    if title:
        with get_db() as conn:
            conn.execute(FUN["create"], (title, due))
            conn.commit()
    return redirect(url_for("index"))


@app.post("/toggle/<int:todo_id>")
def toggle(todo_id: int):
    with get_db() as conn:
        conn.execute(FUN["toggle"], (todo_id,))
        conn.commit()
    return redirect(url_for("index"))


@app.post("/delete/<int:todo_id>")
def delete(todo_id: int):
    with get_db() as conn:
        conn.execute(FUN["delete"], (todo_id,))
        conn.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
