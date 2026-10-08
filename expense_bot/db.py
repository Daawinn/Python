"""SQLite storage for the expense bot."""
import sqlite3
from datetime import date, timedelta

DB_PATH = "expenses.db"


def _conn(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=None):
    with _conn(path) as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                day TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS budgets (
                user_id INTEGER PRIMARY KEY,
                monthly REAL NOT NULL
            )"""
        )


def add_expense(user_id, amount, category, note="", day=None, path=None):
    day = day or date.today().isoformat()
    with _conn(path) as c:
        cur = c.execute(
            "INSERT INTO expenses (user_id, amount, category, note, day) VALUES (?,?,?,?,?)",
            (user_id, amount, category.lower(), note, day),
        )
        return cur.lastrowid


def delete_last(user_id, path=None):
    """Delete the user's most recent expense; return it, or None."""
    with _conn(path) as c:
        row = c.execute(
            "SELECT * FROM expenses WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()
        if row:
            c.execute("DELETE FROM expenses WHERE id=?", (row["id"],))
        return row


def list_expenses(user_id, start, end, path=None):
    with _conn(path) as c:
        return c.execute(
            "SELECT * FROM expenses WHERE user_id=? AND day BETWEEN ? AND ? ORDER BY day, id",
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchall()


def totals_by_category(user_id, start, end, path=None):
    with _conn(path) as c:
        return c.execute(
            """SELECT category, SUM(amount) AS total FROM expenses
               WHERE user_id=? AND day BETWEEN ? AND ?
               GROUP BY category ORDER BY total DESC""",
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchall()


def total(user_id, start, end, path=None):
    with _conn(path) as c:
        row = c.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=? AND day BETWEEN ? AND ?",
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchone()
        return row["t"]


def set_budget(user_id, monthly, path=None):
    with _conn(path) as c:
        c.execute(
            "INSERT INTO budgets (user_id, monthly) VALUES (?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET monthly=excluded.monthly",
            (user_id, monthly),
        )


def get_budget(user_id, path=None):
    with _conn(path) as c:
        row = c.execute("SELECT monthly FROM budgets WHERE user_id=?", (user_id,)).fetchone()
        return row["monthly"] if row else None


def month_range(today=None):
    today = today or date.today()
    start = today.replace(day=1)
    nxt = (start + timedelta(days=32)).replace(day=1)
    return start, nxt - timedelta(days=1)
