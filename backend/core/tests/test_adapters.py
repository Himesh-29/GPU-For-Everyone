"""Tests for core authentication adapters."""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings

from core.adapters import MySocialAccountAdapter

User = get_user_model()


class SocialAccountAdapterTests(TestCase):
    """Test custom social account adapter."""

    def setUp(self):
        """Set up test data."""
        self.adapter = MySocialAccountAdapter()
        self.factory = RequestFactory()

    def test_adapter_instantiation(self):
        """MySocialAccountAdapter can be instantiated."""
        self.assertIsNotNone(self.adapter)

    def test_adapter_allows_signup(self):
        """Adapter allows auto signup."""
        request = self.factory.get('/')
        result = self.adapter.is_auto_signup_allowed(request, None)
        self.assertTrue(result)

    def test_populate_user_sets_username_from_login(self):
        """populate_user sets username from social data 'login' field."""
        request = self.factory.get('/')
        mock_sociallogin = MagicMock()
        data = {'login': 'githubuser', 'email': 'test@example.com'}

        with patch.object(
            MySocialAccountAdapter.__bases__[0],
            'populate_user',
            return_value=User(username=''),
        ):
            user = self.adapter.populate_user(request, mock_sociallogin, data)
            self.assertEqual(user.username, 'githubuser')

    def test_populate_user_sets_username_from_email(self):
        """populate_user falls back to email prefix when no login."""
        request = self.factory.get('/')
        mock_sociallogin = MagicMock()
        data = {'email': 'alice@example.com'}

        with patch.object(
            MySocialAccountAdapter.__bases__[0],
            'populate_user',
            return_value=User(username=''),
        ):
            user = self.adapter.populate_user(request, mock_sociallogin, data)
            self.assertEqual(user.username, 'alice')

    def test_populate_user_fallback_to_user(self):
        """populate_user falls back to 'user' when no login or email."""
        request = self.factory.get('/')
        mock_sociallogin = MagicMock()
        data = {}

        with patch.object(
            MySocialAccountAdapter.__bases__[0],
            'populate_user',
            return_value=User(username=''),
        ):
            user = self.adapter.populate_user(request, mock_sociallogin, data)
            self.assertEqual(user.username, 'user')

    def test_populate_user_preserves_existing_username(self):
        """populate_user doesn't override existing username."""
        request = self.factory.get('/')
        mock_sociallogin = MagicMock()
        data = {'login': 'newname'}

        with patch.object(
            MySocialAccountAdapter.__bases__[0],
            'populate_user',
            return_value=User(username='existing'),
        ):
            user = self.adapter.populate_user(request, mock_sociallogin, data)
            self.assertEqual(user.username, 'existing')

    @override_settings(FRONTEND_URL="http://testfrontend.local")
    def test_on_authentication_error_redirects(self):
        """on_authentication_error redirects to frontend login with error."""
        request = self.factory.get('/')
        response = self.adapter.on_authentication_error(
            request, provider="google", error="access_denied",
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("error=oauth_failed", response.url)
        self.assertIn("http://testfrontend.local/login", response.url)
