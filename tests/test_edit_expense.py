"""
Tests for the edit-expense feature (Step 8).

This test module covers:
1. Auth guards: unauthenticated access redirects to login
2. Ownership: cannot edit other user's expenses, returns 404
3. GET form: renders with pre-populated values
4. Validation errors: amount, category, date validation with error messages
5. Value retention: form re-populates on validation error with submitted values
6. POST valid data: updates expense and redirects to profile
7. Optional description: can be cleared/removed
8. Profile integration: Edit links appear for each transaction
"""

import pytest
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
def auth_client_with_expense(auth_client):
    """Create an authenticated client with a test expense."""
    # Add a test expense
    auth_client.post('/expenses/add', data={
        'amount': '50.00',
        'category': 'Food',
        'date': '2026-03-20',
        'description': 'Lunch'
    })
    return auth_client


class TestAuthGuard:
    """Tests for authentication requirements on edit expense page."""

    def test_get_edit_expense_unauthenticated_redirects_to_login(self, client):
        """GET /expenses/1/edit while logged out redirects to /login."""
        response = client.get('/expenses/1/edit')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_post_edit_expense_unauthenticated_redirects_to_login(self, client):
        """POST /expenses/1/edit while logged out redirects to /login."""
        response = client.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 302
        assert '/login' in response.location


class TestOwnership:
    """Tests for expense ownership enforcement."""

    def test_get_edit_nonexistent_expense_returns_404(self, auth_client_with_expense):
        """GET /expenses/999/edit for non-existent expense returns 404."""
        response = auth_client_with_expense.get('/expenses/999/edit')
        assert response.status_code == 404

    def test_get_edit_other_user_expense_returns_404(self, auth_client_with_expense):
        """GET /expenses/1/edit for other user's expense returns 404."""
        # Register and login as a second user
        auth_client_with_expense.post('/register', data={
            'name': 'Second User',
            'email': 'second@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        auth_client_with_expense.post('/login', data={
            'email': 'second@example.com',
            'password': 'testpass123'
        })
        # Try to edit first user's expense
        response = auth_client_with_expense.get('/expenses/1/edit')
        assert response.status_code == 404

    def test_post_edit_nonexistent_expense_returns_404(self, auth_client_with_expense):
        """POST /expenses/999/edit for non-existent expense returns 404."""
        response = auth_client_with_expense.post('/expenses/999/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 404

    def test_post_edit_other_user_expense_returns_404(self, auth_client_with_expense):
        """POST /expenses/1/edit for other user's expense returns 404."""
        # Register and login as a second user
        auth_client_with_expense.post('/register', data={
            'name': 'Second User',
            'email': 'second@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        auth_client_with_expense.post('/login', data={
            'email': 'second@example.com',
            'password': 'testpass123'
        })
        # Try to edit first user's expense
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 404


class TestGetEditExpense:
    """Tests for GET /expenses/<id>/edit when authenticated."""

    def test_get_edit_expense_renders_form(self, auth_client_with_expense):
        """Authenticated GET to /expenses/1/edit returns 200 with form."""
        response = auth_client_with_expense.get('/expenses/1/edit')
        assert response.status_code == 200

    def test_get_edit_expense_contains_form_with_post_method(self, auth_client_with_expense):
        """Response contains form with method POST."""
        response = auth_client_with_expense.get('/expenses/1/edit')
        assert b'<form' in response.data
        assert b'method="POST"' in response.data.lower() or b'method="post"' in response.data.lower()

    def test_get_edit_expense_prepopulates_amount(self, auth_client_with_expense):
        """Amount field is pre-populated with existing value."""
        response = auth_client_with_expense.get('/expenses/1/edit')
        assert b'50.00' in response.data

    def test_get_edit_expense_prepopulates_category(self, auth_client_with_expense):
        """Category dropdown has correct category pre-selected."""
        response = auth_client_with_expense.get('/expenses/1/edit')
        # Should contain "Food" as selected option
        assert b'Food' in response.data
        # The selected option should be indicated
        assert b'selected' in response.data.lower()

    def test_get_edit_expense_prepopulates_date(self, auth_client_with_expense):
        """Date field is pre-populated with existing value."""
        response = auth_client_with_expense.get('/expenses/1/edit')
        assert b'2026-03-20' in response.data

    def test_get_edit_expense_prepopulates_description(self, auth_client_with_expense):
        """Description field is pre-populated with existing value."""
        response = auth_client_with_expense.get('/expenses/1/edit')
        assert b'Lunch' in response.data

    def test_get_edit_expense_contains_all_category_options(self, auth_client_with_expense):
        """Category dropdown contains all 7 options."""
        response = auth_client_with_expense.get('/expenses/1/edit')

        # Check for all 7 fixed categories
        assert b'Food' in response.data
        assert b'Transport' in response.data
        assert b'Bills' in response.data
        assert b'Health' in response.data
        assert b'Entertainment' in response.data
        assert b'Shopping' in response.data
        assert b'Other' in response.data


class TestPostEditExpenseValidData:
    """Tests for POST /expenses/<id>/edit with valid data."""

    def test_post_edit_expense_valid_data_redirects_to_profile(self, auth_client_with_expense):
        """Updating expense with valid data redirects to /profile."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '75.00',
            'category': 'Transport',
            'date': '2026-03-25',
            'description': 'Updated lunch'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/profile' in response.location

    def test_post_edit_expense_updates_database(self, auth_client_with_expense):
        """Valid submission updates expense record in database."""
        # Update expense
        auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '75.00',
            'category': 'Transport',
            'date': '2026-03-25',
            'description': 'Updated lunch'
        })

        # Verify in database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = 1")
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None
        assert expense['amount'] == 75.00
        assert expense['category'] == 'Transport'
        assert expense['date'] == '2026-03-25'
        assert expense['description'] == 'Updated lunch'

    def test_post_edit_expense_without_description_clears_description(self, auth_client_with_expense):
        """Updating expense without description clears the description field."""
        # Update expense without description
        auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-20',
            'description': ''
        })

        # Verify in database - description should be NULL
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = 1")
        expense = cursor.fetchone()
        conn.close()

        assert expense is not None
        assert expense['description'] is None


class TestPostEditExpenseValidationErrors:
    """Tests for validation error handling."""

    def test_post_edit_expense_missing_amount_shows_error(self, auth_client_with_expense):
        """Missing amount re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Amount' in response.data
        assert b'required' in response.data.lower()

    def test_post_edit_expense_zero_amount_shows_error(self, auth_client_with_expense):
        """Amount of zero re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '0',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'positive' in response.data.lower()

    def test_post_edit_expense_negative_amount_shows_error(self, auth_client_with_expense):
        """Negative amount re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '-10',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'positive' in response.data.lower()

    def test_post_edit_expense_non_numeric_amount_shows_error(self, auth_client_with_expense):
        """Non-numeric amount re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': 'abc',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'valid number' in response.data.lower()

    def test_post_edit_expense_missing_category_shows_error(self, auth_client_with_expense):
        """Missing category re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': '',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Category' in response.data
        assert b'required' in response.data.lower()

    def test_post_edit_expense_invalid_category_shows_error(self, auth_client_with_expense):
        """Invalid category re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'InvalidCategory',
            'date': '2026-03-20',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Invalid' in response.data

    def test_post_edit_expense_missing_date_shows_error(self, auth_client_with_expense):
        """Missing date re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '',
            'description': 'Lunch'
        })
        assert response.status_code == 200
        assert b'Date' in response.data
        assert b'required' in response.data.lower()

    def test_post_edit_expense_invalid_date_format_shows_error(self, auth_client_with_expense):
        """Invalid date format re-renders form with error message."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
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

    def test_value_retention_amount(self, auth_client_with_expense):
        """Amount value is retained after validation error."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '99.00',
            'category': '',
            'date': '2026-03-20',
            'description': 'Test'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'99.00' in response.data

    def test_value_retention_category(self, auth_client_with_expense):
        """Category value is retained after validation error."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'Transport',
            'date': '',
            'description': 'Test'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Transport' in response.data

    def test_value_retention_date(self, auth_client_with_expense):
        """Date value is retained after validation error."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-03-25',
            'description': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'2026-03-25' in response.data

    def test_value_retention_description(self, auth_client_with_expense):
        """Description value is retained after validation error."""
        response = auth_client_with_expense.post('/expenses/1/edit', data={
            'amount': '',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'My lunch'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'My lunch' in response.data


class TestProfileIntegration:
    """Tests for Edit links on profile page."""

    def test_profile_has_actions_column(self, auth_client_with_expense):
        """Profile page contains Actions column header."""
        response = auth_client_with_expense.get('/profile')
        assert response.status_code == 200
        assert b'Actions' in response.data

    def test_profile_has_edit_link_per_transaction(self, auth_client_with_expense):
        """Profile page contains Edit link for each transaction."""
        response = auth_client_with_expense.get('/profile')
        assert response.status_code == 200
        assert b'Edit' in response.data

    def test_profile_edit_link_points_to_correct_url(self, auth_client_with_expense):
        """Edit link points to /expenses/<id>/edit."""
        response = auth_client_with_expense.get('/profile')
        assert b'/expenses/1/edit' in response.data


class TestDatabaseFunctions:
    """Tests for database query functions."""

    def test_get_expense_by_id_returns_expense(self, app):
        """get_expense_by_id returns expense when it exists and belongs to user."""
        with app.app_context():
            from database.db import get_expense_by_id, create_expense

            # Create user and expense
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ('Test User', 'testdb@example.com', 'hash')
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            expense_id = create_expense(user_id, 50.00, 'Food', '2026-03-20', 'Test')

            # Fetch expense
            expense = get_expense_by_id(expense_id, user_id)

            assert expense is not None
            assert expense['id'] == expense_id
            assert expense['amount'] == 50.00
            assert expense['category'] == 'Food'

    def test_get_expense_by_id_returns_none_for_wrong_user(self, app):
        """get_expense_by_id returns None when expense belongs to different user."""
        with app.app_context():
            from database.db import get_expense_by_id, create_expense

            # Create two users
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ('User 1', 'user1@example.com', 'hash')
            )
            user1_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ('User 2', 'user2@example.com', 'hash')
            )
            user2_id = cursor.lastrowid
            conn.commit()
            conn.close()

            expense_id = create_expense(user1_id, 50.00, 'Food', '2026-03-20', 'Test')

            # Try to fetch as user2
            expense = get_expense_by_id(expense_id, user2_id)

            assert expense is None

    def test_get_expense_by_id_returns_none_for_nonexistent(self, app):
        """get_expense_by_id returns None for non-existent expense."""
        with app.app_context():
            from database.db import get_expense_by_id

            expense = get_expense_by_id(999, 1)

            assert expense is None

    def test_update_expense_updates_row(self, app):
        """update_expense updates expense when it exists and belongs to user."""
        with app.app_context():
            from database.db import get_expense_by_id, create_expense, update_expense

            # Create user and expense
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ('Test User', 'testupdate@example.com', 'hash')
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            expense_id = create_expense(user_id, 50.00, 'Food', '2026-03-20', 'Test')

            # Update expense
            rows = update_expense(expense_id, user_id, 99.00, 'Transport', '2026-03-25', 'Updated')

            assert rows == 1

            # Verify update
            expense = get_expense_by_id(expense_id, user_id)
            assert expense['amount'] == 99.00
            assert expense['category'] == 'Transport'
            assert expense['description'] == 'Updated'

    def test_update_expense_returns_zero_for_wrong_user(self, app):
        """update_expense returns 0 when expense belongs to different user."""
        with app.app_context():
            from database.db import create_expense, update_expense

            # Create two users
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ('User 1', 'user1up@example.com', 'hash')
            )
            user1_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ('User 2', 'user2up@example.com', 'hash')
            )
            user2_id = cursor.lastrowid
            conn.commit()
            conn.close()

            expense_id = create_expense(user1_id, 50.00, 'Food', '2026-03-20', 'Test')

            # Try to update as user2
            rows = update_expense(expense_id, user2_id, 99.00, 'Transport', '2026-03-25', 'Hacked')

            assert rows == 0