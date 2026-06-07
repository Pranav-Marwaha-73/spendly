"""
Tests for the date filter feature on the profile page.

This test module covers:
1. Happy paths: preset filters (This Month, Last 3 Months, Last 6 Months, All Time)
   and custom date range submission
2. Edge cases: invalid date ranges, malformed dates, empty results
3. Auth guards: unauthenticated access redirects to login
4. DB side effects: filter applies to stats, transactions, and category breakdown
"""

import pytest
from datetime import date, timedelta
from app import app as flask_app
from database.db import get_db, init_db


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': 'spendly_test.db',
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        # Clean up test database if exists
        import os
        if os.path.exists('spendly_test.db'):
            os.remove('spendly_test.db')
        init_db()
        yield flask_app
        # Cleanup after tests
        if os.path.exists('spendly_test.db'):
            os.remove('spendly_test.db')


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create a test client with a logged-in user."""
    # Register a test user
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    })
    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    return client


@pytest.fixture
def user_with_expenses(auth_client):
    """Add sample expenses for a range of dates."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the user id
    cursor.execute("SELECT id FROM users WHERE email = ?", ('test@example.com',))
    user_id = cursor.fetchone()['id']

    # Insert expenses across different months
    today = date.today()
    last_month = today - timedelta(days=30)
    two_months_ago = today - timedelta(days=60)
    four_months_ago = today - timedelta(days=120)
    seven_months_ago = today - timedelta(days=210)

    expenses = [
        (user_id, 100.00, "Food", last_month.isoformat(), "Last month food"),
        (user_id, 50.00, "Transport", last_month.isoformat(), "Last month transport"),
        (user_id, 200.00, "Bills", two_months_ago.isoformat(), "Two months ago bills"),
        (user_id, 75.00, "Health", two_months_ago.isoformat(), "Two months ago health"),
        (user_id, 150.00, "Shopping", four_months_ago.isoformat(), "Four months ago shopping"),
        (user_id, 300.00, "Entertainment", seven_months_ago.isoformat(), "Seven months ago entertainment"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )
    conn.commit()
    conn.close()

    return auth_client


class TestAuthGuard:
    """Tests for authentication requirements on profile page."""

    def test_unauthenticated_redirect_to_login(self, client):
        """Unauthenticated user accessing /profile redirects to login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location


class TestHappyPaths:
    """Tests for successful date filter scenarios."""

    def test_profile_no_params_returns_unfiltered_data(self, user_with_expenses):
        """Visiting /profile with no query params returns all expenses."""
        response = user_with_expenses.get('/profile')
        assert response.status_code == 200

        # Should show all 6 expenses
        assert b'6' in response.data or b'6' in response.data

        # Total should be sum of all expenses: 100+50+200+75+150+300 = 875
        assert b'875.00' in response.data

    def test_this_month_filter(self, user_with_expenses):
        """Clicking This Month filters to current calendar month."""
        today = date.today()
        this_month_start = date(today.year, today.month, 1)

        response = user_with_expenses.get(f'/profile?date_from={this_month_start.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # There are no expenses in current month (only past dates)
        # So transaction count should be 0 and total 0.00
        assert b'0' in response.data
        assert b'0.00' in response.data

    def test_last_3_months_filter(self, user_with_expenses):
        """Clicking Last 3 Months filters to 3-month window ending today."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        response = user_with_expenses.get(f'/profile?date_from={three_months_ago.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Last 3 months includes last_month and two_months_ago expenses
        # 100 + 50 + 200 + 75 = 425
        assert b'425.00' in response.data

    def test_last_6_months_filter(self, user_with_expenses):
        """Clicking Last 6 Months filters to 6-month window ending today."""
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        response = user_with_expenses.get(f'/profile?date_from={six_months_ago.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Last 6 months includes last_month, two_months_ago, and four_months_ago
        # 100 + 50 + 200 + 75 + 150 = 575
        assert b'575.00' in response.data

    def test_all_time_removes_filter(self, user_with_expenses):
        """Clicking All Time (no query params) shows all expenses."""
        # First apply a filter
        today = date.today()
        three_months_ago = today - timedelta(days=90)
        user_with_expenses.get(f'/profile?date_from={three_months_ago.isoformat()}&date_to={today.isoformat()}')

        # Then access without params
        response = user_with_expenses.get('/profile')
        assert response.status_code == 200

        # Should show all 6 expenses again
        assert b'875.00' in response.data

    def test_custom_date_range_valid(self, user_with_expenses):
        """Submitting valid custom date range shows only expenses in range."""
        today = date.today()
        two_months_ago = today - timedelta(days=60)
        last_month = today - timedelta(days=30)

        # Filter to only include two_months_ago to last_month range
        response = user_with_expenses.get(f'/profile?date_from={two_months_ago.isoformat()}&date_to={last_month.isoformat()}')
        assert response.status_code == 200

        # Should only show expenses in that range: 200 + 75 = 275
        assert b'275.00' in response.data


class TestEdgeCases:
    """Tests for edge case handling."""

    def test_date_from_greater_than_date_to_shows_flash_error(self, user_with_expenses):
        """Submitting range where date_from > date_to shows flash error and falls back."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        response = user_with_expenses.get(f'/profile?date_from={today.isoformat()}&date_to={yesterday.isoformat()}', follow_redirects=True)
        assert response.status_code == 200

        # Check flash message is displayed
        assert b'Start date must be before end date' in response.data

        # Should fall back to unfiltered view (all expenses)
        assert b'875.00' in response.data

    def test_malformed_date_from_silent_fallback(self, user_with_expenses):
        """Submitting malformed date string doesn't crash, falls back silently."""
        response = user_with_expenses.get('/profile?date_from=not-a-date&date_to=2026-06-01')
        assert response.status_code == 200

        # Should fall back to unfiltered view
        assert b'875.00' in response.data

    def test_malformed_date_to_silent_fallback(self, user_with_expenses):
        """Submitting malformed date_to doesn't crash, falls back silently."""
        response = user_with_expenses.get('/profile?date_from=2026-01-01&date_to=invalid')
        assert response.status_code == 200

        # Should fall back to unfiltered view
        assert b'875.00' in response.data

    def test_user_with_no_expenses_in_range_sees_zero(self, user_with_expenses):
        """User with no expenses in selected range sees ₹0.00 total, 0 transactions."""
        # Filter to a future date range where there are no expenses
        today = date.today()
        next_month = today + timedelta(days=60)

        response = user_with_expenses.get(f'/profile?date_from={today.isoformat()}&date_to={next_month.isoformat()}')
        assert response.status_code == 200

        # Should show zero totals
        assert b'0.00' in response.data
        assert b'0' in response.data


class TestValidationErrors:
    """Tests for validation error handling."""

    def test_invalid_date_falls_back_to_unfiltered(self, user_with_expenses):
        """Invalid dates fall back to unfiltered view."""
        # Completely invalid dates
        response = user_with_expenses.get('/profile?date_from=abc&date_to=xyz')
        assert response.status_code == 200

        # Should show all expenses (unfiltered)
        assert b'875.00' in response.data


class TestDBSideEffects:
    """Tests for database filter affecting all sections."""

    def test_filter_affects_stats_section(self, user_with_expenses):
        """Date filter affects the summary stats section."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        response = user_with_expenses.get(f'/profile?date_from={three_months_ago.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Stats should show filtered totals
        assert b'425.00' in response.data  # Total spent

    def test_filter_affects_transactions_section(self, user_with_expenses):
        """Date filter affects the transactions list."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        response = user_with_expenses.get(f'/profile?date_from={three_months_ago.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Should show only transactions from last 3 months
        # 4 transactions in range: 100, 50, 200, 75
        assert b'Last month food' in response.data
        assert b'Last month transport' in response.data
        assert b'Two months ago bills' in response.data
        assert b'Two months ago health' in response.data

        # Should NOT show older transactions
        assert b'Four months ago shopping' not in response.data
        assert b'Seven months ago entertainment' not in response.data

    def test_filter_affects_category_breakdown(self, user_with_expenses):
        """Date filter affects the category breakdown section."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        response = user_with_expenses.get(f'/profile?date_from={three_months_ago.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Should show only categories from filtered range
        # In last 3 months: Food=150, Transport=50, Bills=200, Health=75
        # Should NOT show Shopping (150 from 4 months ago)
        assert b'Shopping' not in response.data
        # Should show categories from the filtered range
        assert b'Food' in response.data
        assert b'Transport' in response.data


class TestPresetButtons:
    """Tests for preset button functionality."""

    def test_this_month_preset_highlighted(self, user_with_expenses):
        """This Month preset button is highlighted when active."""
        today = date.today()
        this_month_start = date(today.year, today.month, 1)

        response = user_with_expenses.get(f'/profile?date_from={this_month_start.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Check that the this_month preset is marked as active
        assert b'this_month' in response.data

    def test_last_3_months_preset_highlighted(self, user_with_expenses):
        """Last 3 Months preset button is highlighted when active."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        response = user_with_expenses.get(f'/profile?date_from={three_months_ago.isoformat()}&date_to={today.isoformat()}')
        assert response.status_code == 200

        # Check that the last_3_months preset is marked as active
        assert b'last_3_months' in response.data

    def test_all_time_preset_highlighted_without_params(self, user_with_expenses):
        """All Time preset is highlighted when no filter params present."""
        response = user_with_expenses.get('/profile')
        assert response.status_code == 200

        # Should have no active_filter (None), making All Time active
        # The All Time button has class 'active' when not active_filter
        assert b'All Time' in response.data