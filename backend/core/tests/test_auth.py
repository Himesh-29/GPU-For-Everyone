"""
Test Suite: Authentication & User Registration
Covers: POST /api/core/register/, POST /api/core/token/, GET /api/core/profile/
Including: Password strength validation
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import User


@pytest.mark.django_db
class TestRegistration:
    """Tests for POST /api/core/register/"""

    def setup_method(self):
        self.client = APIClient()

    def test_register_success(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'X*92kjLmn!q',
            'role': 'USER'
        }, format='json')
        assert resp.status_code == 201
        assert User.objects.filter(username='newuser').exists()

    def test_register_creates_user_with_default_balance(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('register'), {
            'username': 'rich',
            'email': 'rich@test.com',
            'password': 'X*92kjLmn!q',
        }, format='json')
        user = User.objects.get(username='rich')
        assert user.wallet_balance == Decimal('100.00')

    def test_register_with_provider_role(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('register'), {
            'username': 'gpugod',
            'email': 'gpu@test.com',
            'password': 'X*92kjLmn!q',
            'role': 'PROVIDER'
        }, format='json')
        user = User.objects.get(username='gpugod')
        assert user.role == 'PROVIDER'

    def test_register_duplicate_username_fails(self):  # pylint: disable=missing-function-docstring
        User.objects.create_user(username='taken', password='X*92kjLmn!q')
        resp = self.client.post(reverse('register'), {
            'username': 'taken',
            'email': 'dupe@test.com',
            'password': 'X*92kjLmn!q',
        }, format='json')
        assert resp.status_code == 400

    def test_register_missing_password_fails(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('register'), {
            'username': 'nopass',
            'email': 'nopass@test.com',
        }, format='json')
        assert resp.status_code == 400

    def test_register_missing_username_fails(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('register'), {
            'email': 'noname@test.com',
            'password': 'X*92kjLmn!q',
        }, format='json')
        assert resp.status_code == 400

    # --- Password Validation ---
    def test_short_password_rejected(self):
        """Django validators reject passwords under 8 chars."""
        resp = self.client.post(reverse('register'), {
            'username': 'shortpw',
            'email': 'a@b.com',
            'password': 'Ab1!',
        }, format='json')
        assert resp.status_code == 400

    def test_common_password_rejected(self):
        """Django validators reject common passwords like 'password123'."""
        resp = self.client.post(reverse('register'), {
            'username': 'commonpw',
            'email': 'c@d.com',
            'password': 'password123',
        }, format='json')
        assert resp.status_code == 400

    def test_numeric_only_password_rejected(self):
        """Django validators reject all-numeric passwords."""
        resp = self.client.post(reverse('register'), {
            'username': 'numericpw',
            'email': 'e@f.com',
            'password': '12345678',
        }, format='json')
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogin:
    """Tests for POST /api/core/token/"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='alice', password='X*92kjLmn!q')

    def test_login_success(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('token_obtain_pair'), {
            'username': 'alice',
            'password': 'X*92kjLmn!q'
        }, format='json')
        assert resp.status_code == 200
        assert 'access' in resp.data
        assert 'refresh' in resp.data

    def test_login_wrong_password(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('token_obtain_pair'), {
            'username': 'alice',
            'password': 'wrongpassword'
        }, format='json')
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('token_obtain_pair'), {
            'username': 'ghost',
            'password': 'whatever123'
        }, format='json')
        assert resp.status_code == 401


@pytest.mark.django_db
class TestProfile:
    """Tests for GET /api/core/profile/"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='profileuser', password='X*92kjLmn!q',
            email='profile@test.com', role='PROVIDER',
            wallet_balance=Decimal('42.50')
        )

    def test_get_profile_authenticated(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(reverse('profile'))
        assert resp.status_code == 200
        assert resp.data['username'] == 'profileuser'
        assert resp.data['email'] == 'profile@test.com'
        assert resp.data['role'] == 'PROVIDER'

    def test_get_profile_unauthenticated(self):  # pylint: disable=missing-function-docstring
        resp = self.client.get(reverse('profile'))
        assert resp.status_code == 401

    def test_profile_includes_wallet_balance(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(reverse('profile'))
        assert 'wallet_balance' in resp.data

    def test_profile_wallet_balance_correct(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(reverse('profile'))
        assert Decimal(resp.data['wallet_balance']) == Decimal('42.50')
