import sqlite3
from datetime import datetime, date
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


@app.route("/analytics")
def analytics():
    # Redirect to login if not authenticated
    if not is_logged_in():
        return redirect(url_for("login"))

    return render_template("analytics.html", active_page="analytics")


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

    # Parse and validate date filter parameters
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    active_filter = None

    # Validate date_from
    if date_from:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            date_from = None

    # Validate date_to
    if date_to:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            date_to = None

    # Check if date_from > date_to
    if date_from and date_to:
        from_dt = datetime.strptime(date_from, "%Y-%m-%d").date()
        to_dt = datetime.strptime(date_to, "%Y-%m-%d").date()
        if from_dt > to_dt:
            flash("Start date must be before end date.")
            date_from = None
            date_to = None

    # Compute preset date ranges
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    last_3_months_start = today.replace(day=1)
    from datetime import timedelta
    last_3_months_start = (today - timedelta(days=90))
    last_6_months_start = (today - timedelta(days=180))

    presets = {
        "this_month": {
            "date_from": this_month_start.isoformat(),
            "date_to": today.isoformat(),
            "label": "This Month"
        },
        "last_3_months": {
            "date_from": last_3_months_start.isoformat(),
            "date_to": today.isoformat(),
            "label": "Last 3 Months"
        },
        "last_6_months": {
            "date_from": last_6_months_start.isoformat(),
            "date_to": today.isoformat(),
            "label": "Last 6 Months"
        }
    }

    # Determine active filter for highlighting
    if date_from and date_to:
        # Check if matches a preset
        for key, preset in presets.items():
            if preset["date_from"] == date_from and preset["date_to"] == date_to:
                active_filter = key
                break
        if not active_filter:
            active_filter = "custom"

    stats = get_user_stats(user_id, date_from, date_to)

    # Get transactions from database
    raw_transactions = get_user_expenses(user_id, date_from, date_to)
    transactions = [
        {
            "date": format_date_for_display(t["date"]),
            "description": t["description"],
            "category": t["category"],
            "amount": t["amount"]
        }
        for t in raw_transactions
    ]

    categories = get_category_breakdown(user_id, date_from, date_to)

    return render_template("profile.html",
                         user=user,
                         stats=stats,
                         transactions=transactions,
                         categories=categories,
                         date_from=date_from,
                         date_to=date_to,
                         active_filter=active_filter,
                         presets=presets,
                         active_page="profile")


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
