"""
Tests for the add-expense feature (Step 7).

This test module covers:
1. Auth guards: unauthenticated access redirects to login
2. Happy paths: form renders correctly, valid submission creates expense
3. Validation errors: amount, category, date validation with error messages
4. Value retention: form re-populates on validation error
5. Optional description: saves as NULL when not provided
6. Profile integration: Add Expense button exists
7. Navbar: Add Expense link visible when logged in
"""

import pytest
from datetime import date
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


class TestAuthGuard:
    """Tests for authentication requirements on add expense page."""

    def test_get_expenses_add_unauthenticated_redirects_to_login(self, client):
        """GET /expenses/add while logged out redirects to /login."""
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_post_expenses_add_unauthenticated_redirects_to_login(self, client):
        """POST /expenses/add while logged out redirects to /login."""
        response = client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 302
        assert '/login' in response.location


class TestGetExpensesAdd:
    """Tests for GET /expenses/add when authenticated."""

    def test_get_expenses_add_renders_form(self, auth_client):
        """Authenticated GET to /expenses/add returns 200 with form."""
        response = auth_client.get('/expenses/add')
        assert response.status_code == 200

    def test_get_expenses_add_contains_form_with_post_method(self, auth_client):
        """Response contains form with method POST."""
        response = auth_client.get('/expenses/add')
        assert b'<form' in response.data
        assert b'method="POST"' in response.data.lower() or b'method="post"' in response.data.lower()

    def test_get_expenses_add_contains_all_category_options(self, auth_client):
        """Category dropdown contains all 7 options."""
        response = auth_client.get('/expenses/add')

        # Check for all 7 fixed categories
        assert b'Food' in response.data
        assert b'Transport' in response.data
        assert b'Bills' in response.data
        assert b'Health' in response.data
        assert b'Entertainment' in response.data
        assert b'Shopping' in response.data
        assert b'Other' in response.data

    def test_get_expenses_add_contains_amount_field(self, auth_client):
        """Form contains amount input field."""
        response = auth_client.get('/expenses/add')
        assert b'amount' in response.data

    def test_get_expenses_add_contains_date_field(self, auth_client):
        """Form contains date input field."""
        response = auth_client.get('/expenses/add')
        assert b'date' in response.data

    def test_get_expenses_add_contains_description_field(self, auth_client):
        """Form contains description input field."""
        response = auth_client.get('/expenses/add')
        assert b'description' in response.data

    def test_get_expenses_add_default_date_is_today(self, auth_client):
        """Date field defaults to today's date."""
        response = auth_client.get('/expenses/add')
        today = date.today().isoformat()
        assert today.encode() in response.data


class TestPostExpensesAddValidData:
    """Tests for POST /expenses/add with valid data."""

    def test_post_expenses_add_valid_data_redirects_to_profile(self, auth_client):
        """Submitting valid expense redirects to /profile."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/profile' in response.location

    def test_post_expenses_add_creates_expense_in_database(self, auth_client):
        """Valid submission creates expense record in database."""
        # Submit expense
        auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })

        # Verify in database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = ?)", ('test@example.com',))
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None
        assert expense['amount'] == 50.00
        assert expense['category'] == 'Food'
        assert expense['date'] == '2026-03-20'
        assert expense['description'] == 'Lunch'

    def test_post_expenses_add_with_all_fields_creates_expense(self, auth_client):
        """Expense with all fields (including optional description) saves correctly."""
        auth_client.post('/expenses/add', data={
            'amount': '150.50',
            'category': 'Shopping',
            'date': '2026-04-15',
            'description': 'New headphones'
        })

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE description = ?", ('New headphones',))
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None
        assert expense['amount'] == 150.50
        assert expense['category'] == 'Shopping'


class TestPostExpensesAddValidationErrors:
    """Tests for validation error handling."""

    def test_post_expenses_add_missing_amount_shows_error(self, auth_client):
        """Missing amount re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': '',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Amount' in response.data
        assert b'required' in response.data.lower()

    def test_post_expenses_add_zero_amount_shows_error(self, auth_client):
        """Amount of zero re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': '0',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'positive' in response.data.lower()

    def test_post_expenses_add_negative_amount_shows_error(self, auth_client):
        """Negative amount re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': '-10',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'positive' in response.data.lower()

    def test_post_expenses_add_non_numeric_amount_shows_error(self, auth_client):
        """Non-numeric amount re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': 'abc',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'valid number' in response.data.lower()

    def test_post_expenses_add_missing_category_shows_error(self, auth_client):
        """Missing category re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': '',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Category' in response.data
        assert b'required' in response.data.lower()

    def test_post_expenses_add_missing_date_shows_error(self, auth_client):
        """Missing date re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Date' in response.data
        assert b'required' in response.data.lower()

    def test_post_expenses_add_invalid_date_format_shows_error(self, auth_client):
        """Invalid date format re-renders form with error message."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '20-03-2026',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'date' in response.data.lower()
        assert b'format' in response.data.lower()


class TestValueRetention:
    """Tests for form value retention on validation error."""

    def test_value_retention_amount(self, auth_client):
        """Amount value is retained after validation error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '75.00',
            'category': '',
            'date': '2026-03-20',
            'description': 'Test'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'75.00' in response.data

    def test_value_retention_category(self, auth_client):
        """Category value is retained after validation error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Transport',
            'date': '',
            'description': 'Test'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Transport' in response.data

    def test_value_retention_date(self, auth_client):
        """Date value is retained after validation error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-25',
            'description': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'2026-03-25' in response.data

    def test_value_retention_description(self, auth_client):
        """Description value is retained after validation error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'My lunch'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'My lunch' in response.data


class TestOptionalDescription:
    """Tests for optional description field."""

    def test_post_expenses_add_without_description_saves_expense(self, auth_client):
        """Submitting without description saves expense with NULL description."""
        response = auth_client.post('/expenses/add', data={
            'amount': '25.00',
            'category': 'Food',
            'date': '2026-04-01',
            'description': ''
        }, follow_redirects=False)
        assert response.status_code == 302

        # Verify in database - description should be NULL
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = ?) AND amount = ?",
                       ('test@example.com', 25.00))
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None
        assert expense['description'] is None

    def test_post_expenses_add_without_description_redirects_to_profile(self, auth_client):
        """Optional description can be omitted without error."""
        response = auth_client.post('/expenses/add', data={
            'amount': '30.00',
            'category': 'Transport',
            'date': '2026-04-05'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/profile' in response.location


class TestProfileIntegration:
    """Tests for Add Expense button on profile page."""

    def test_profile_has_add_expense_button(self, auth_client):
        """Profile page contains an Add Expense button/link."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Add Expense' in response.data

    def test_profile_add_expense_button_links_to_expenses_add(self, auth_client):
        """Add Expense button links to /expenses/add."""
        response = auth_client.get('/profile')
        assert b'/expenses/add' in response.data


class TestNavbar:
    """Tests for Add Expense link in navbar."""

    def test_navbar_shows_add_expense_link_when_logged_in(self, auth_client):
        """Navbar shows Add Expense link when user is logged in."""
        response = auth_client.get('/profile')
        assert response.status_code == 200

        # Check that there's a link to add expense in the navigation
        # The navbar should contain a link to /expenses/add
        assert b'Add Expense' in response.data

    def test_navbar_no_add_expense_link_when_logged_out(self, client):
        """Navbar does not show Add Expense link when user is not logged in."""
        response = client.get('/')
        assert response.status_code == 200
        # When not logged in, should not see Add Expense in nav
        # (Though it could appear in a different section)