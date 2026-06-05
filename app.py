import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email, get_user_expenses, get_user_stats, get_category_breakdown

app = Flask(__name__)
app.secret_key = "dev-secret-key-for-spendly"


def is_logged_in():
    return "user_id" in session


@app.context_processor
def inject_user():
    return dict(is_logged_in=is_logged_in())


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if is_logged_in():
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")

        try:
            create_user(name, email, password)
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Email already registered")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Invalid email or password.")

        user = get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def format_date_for_display(date_str):
    """Convert YYYY-MM-DD to 'MMM DD, YYYY' format (e.g., 'May 15, 2026')"""
    from datetime import datetime
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")


@app.route("/profile")
def profile():
    # Redirect to login if not authenticated
    if not is_logged_in():
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Get user info from database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, created_at FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()

    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "created_at": "January 2026",
        "initials": "".join([n[0] for n in user_row["name"].split()])
    }

    stats = get_user_stats(user_id)

    # Get transactions from database
    raw_transactions = get_user_expenses(user_id)
    transactions = [
        {
            "date": format_date_for_display(t["date"]),
            "description": t["description"],
            "category": t["category"],
            "amount": t["amount"]
        }
        for t in raw_transactions
    ]

    categories = get_category_breakdown(user_id)

    return render_template("profile.html",
                         user=user,
                         stats=stats,
                         transactions=transactions,
                         categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
