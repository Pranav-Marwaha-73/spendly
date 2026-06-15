import sqlite3
from werkzeug.security import generate_password_hash


def get_db():
    conn = sqlite3.connect("spendly.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Insert demo user
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123"))
    )
    user_id = cursor.lastrowid

    # Insert 8 sample expenses
    expenses = [
        (user_id, 45.50, "Food", "2026-05-02", "Grocery shopping"),
        (user_id, 25.00, "Transport", "2026-05-05", "Uber ride"),
        (user_id, 120.00, "Bills", "2026-05-08", "Electricity bill"),
        (user_id, 80.00, "Health", "2026-05-10", "Doctor visit"),
        (user_id, 35.00, "Entertainment", "2026-05-12", "Movie tickets"),
        (user_id, 150.00, "Shopping", "2026-05-15", "New shoes"),
        (user_id, 20.00, "Food", "2026-05-17", "Coffee and snacks"),
        (user_id, 55.00, "Other", "2026-05-18", "Miscellaneous"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )

    conn.commit()
    conn.close()


def create_user(name, email, password):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_expenses(user_id, date_from=None, date_to=None):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, date, description, category, amount FROM expenses WHERE user_id = ?"
    params = [user_id]

    if date_from and date_to:
        query += " AND date BETWEEN ? AND ?"
        params.extend([date_from, date_to])

    query += " ORDER BY date DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    cursor = conn.cursor()

    base_where = "WHERE user_id = ?"
    params = [user_id]

    if date_from and date_to:
        base_where += " AND date BETWEEN ? AND ?"
        params.extend([date_from, date_to])

    # Get total_spent and transaction_count
    cursor.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count FROM expenses {base_where}",
        params
    )
    row = cursor.fetchone()
    total_spent = row["total_spent"] if row else 0
    transaction_count = row["transaction_count"] if row else 0

    # Get top_category (category with highest total amount)
    cursor.execute(
        f"SELECT category FROM expenses {base_where} GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        params
    )
    top_category_row = cursor.fetchone()
    top_category = top_category_row["category"] if top_category_row else None

    conn.close()

    return {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category
    }


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?"
    params = [user_id]

    if date_from and date_to:
        query += " AND date BETWEEN ? AND ?"
        params.extend([date_from, date_to])

    query += " GROUP BY category ORDER BY total DESC"

    # Get category totals and grand total
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    # Calculate grand total
    grand_total = sum(row["total"] for row in rows)

    # Build result with percentages
    breakdown = []
    for row in rows:
        category_total = row["total"]
        percentage = round((category_total / grand_total) * 100)
        breakdown.append({
            "name": row["category"],
            "amount": category_total,
            "percentage": percentage
        })

    return breakdown


def create_expense(user_id, amount, category, date, description=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description)
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def update_expense(expense_id, user_id, amount, category, date, description=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?",
        (amount, category, date, description, expense_id, user_id)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected


def delete_expense(expense_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    conn.commit()
    conn.close()