import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

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


@app.route("/profile")
def profile():
    # Redirect to login if not authenticated
    if not is_logged_in():
        return redirect(url_for("login"))

    # Hardcoded data (will be replaced with DB queries in Step 5)
    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "created_at": "January 2026",
        "initials": "DU"
    }

    stats = {
        "total_spent": 1234.56,
        "transaction_count": 24,
        "top_category": "Food"
    }

    transactions = [
        {"date": "May 15, 2026", "description": "Grocery shopping", "category": "Food", "amount": 45.50},
        {"date": "May 12, 2026", "description": "Uber ride", "category": "Transport", "amount": 25.00},
        {"date": "May 08, 2026", "description": "Electricity bill", "category": "Bills", "amount": 120.00},
        {"date": "May 05, 2026", "description": "Doctor visit", "category": "Health", "amount": 80.00},
        {"date": "May 02, 2026", "description": "Movie tickets", "category": "Entertainment", "amount": 35.00}
    ]

    categories = [
        {"name": "Food", "amount": 450.00, "percentage": 36},
        {"name": "Transport", "amount": 250.00, "percentage": 20},
        {"name": "Bills", "amount": 200.00, "percentage": 16},
        {"name": "Shopping", "amount": 150.00, "percentage": 12},
        {"name": "Health", "amount": 100.00, "percentage": 8}
    ]

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
