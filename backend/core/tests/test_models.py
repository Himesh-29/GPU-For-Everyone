"""
Test Suite: Core User Model and AgentToken
Covers: User creation, password hashing, wallet defaults, token generation/validation
"""
from decimal import Decimal

import pytest

from core.models import User, AgentToken


@pytest.mark.django_db
def test_user_creation():  # pylint: disable=missing-function-docstring
    user = User.objects.create_user(username='testuser', password='password')
    assert user.username == 'testuser'
    assert user.check_password('password')
    assert user.wallet_balance == Decimal('100.00')


@pytest.mark.django_db
def test_wallet_update():  # pylint: disable=missing-function-docstring
    user = User.objects.create_user(username='testuser', password='password')
    user.wallet_balance += Decimal('50.00')
    user.save()
    user.refresh_from_db()
    assert user.wallet_balance == Decimal('150.00')


@pytest.mark.django_db
def test_wallet_deduction():  # pylint: disable=missing-function-docstring
    user = User.objects.create_user(username='spender', password='password')
    user.wallet_balance -= Decimal('25.00')
    user.save()
    user.refresh_from_db()
    assert user.wallet_balance == Decimal('75.00')


# --- AgentToken Tests ---

@pytest.mark.django_db
class TestAgentToken:
    """Tests for AgentToken model."""

    def setup_method(self):  # pylint: disable=missing-function-docstring
        self.user = User.objects.create_user(
            username="tokenuser", password="p",
        )

    def test_generate_returns_token_and_raw(self):
        """generate() returns (AgentToken, raw_token) tuple."""
        agent_token, raw = AgentToken.generate(self.user, label="My Agent")
        assert agent_token.id is not None
        assert raw.startswith("gpc_")
        assert agent_token.label == "My Agent"
        assert agent_token.user == self.user
        assert agent_token.is_active is True

    def test_generate_stores_hash_not_raw(self):
        """generate() stores only the hash, not the raw token."""
        agent_token, raw = AgentToken.generate(self.user)
        assert agent_token.token_hash != raw
        assert agent_token.token_hash == AgentToken.hash_token(raw)

    def test_validate_returns_token_for_valid(self):
        """validate() returns AgentToken for a valid raw token."""
        _, raw = AgentToken.generate(self.user, label="Valid Token")
        result = AgentToken.validate(raw)
        assert result is not None
        assert result.user == self.user
        assert result.last_used is not None

    def test_validate_returns_none_for_invalid(self):
        """validate() returns None for invalid token."""
        result = AgentToken.validate("gpc_doesnotexist123")
        assert result is None

    def test_validate_returns_none_for_revoked(self):
        """validate() returns None for revoked (inactive) token."""
        agent_token, raw = AgentToken.generate(self.user)
        agent_token.is_active = False
        agent_token.save()
        result = AgentToken.validate(raw)
        assert result is None

    def test_str_representation(self):
        """AgentToken.__str__ includes label and username."""
        agent_token, _ = AgentToken.generate(self.user, label="TestLabel")
        s = str(agent_token)
        assert "TestLabel" in s
        assert self.user.username in s

    def test_hash_token_deterministic(self):
        """hash_token returns same hash for same input."""
        h1 = AgentToken.hash_token("gpc_test123")
        h2 = AgentToken.hash_token("gpc_test123")
        assert h1 == h2

    def test_hash_token_different_for_different_input(self):
        """hash_token returns different hash for different input."""
        h1 = AgentToken.hash_token("gpc_aaa")
        h2 = AgentToken.hash_token("gpc_bbb")
        assert h1 != h2
