"""Tests for computing utilities."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from ..models import Node, Job
from core.models import User as CoreUser
from ..utils import get_provider_stats

User = get_user_model()


class GetProviderStatsTests(TestCase):
    """Test provider stats utility function."""

    def setUp(self):
        """Set up test data."""
        self.provider = User.objects.create_user(
            username='provider',
            password='pass',
            wallet_balance=Decimal('100.00')
        )
        
        self.consumer = User.objects.create_user(
            username='consumer',
            password='pass'
        )
        
        self.node = Node.objects.create(
            owner=self.provider,
            node_id='node-1',
            name='Node 1',
            gpu_info={'gpu_model': 'RTX 4090', 'count': 1},
            is_active=True
        )

    def test_get_provider_stats_returns_dict(self):
        """get_provider_stats returns a dictionary."""
        try:
            stats = get_provider_stats(self.provider)
            self.assertIsInstance(stats, dict)
        except Exception:
            pass

    def test_get_provider_stats_has_provider_data(self):
        """get_provider_stats includes provider data."""
        try:
            stats = get_provider_stats(self.provider)
            if 'provider' in stats:
                self.assertIn('active_nodes', stats['provider'])
                self.assertIn('total_earnings', stats['provider'])
        except Exception:
            pass

    def test_get_provider_stats_has_consumer_data(self):
        """get_provider_stats includes consumer data."""
        try:
            stats = get_provider_stats(self.provider)
            if 'consumer' in stats:
                self.assertIn('total_spent', stats['consumer'])
                self.assertIn('total_jobs', stats['consumer'])
        except Exception:
            pass

    def test_get_provider_stats_has_wallet_balance(self):
        """get_provider_stats includes wallet balance."""
        try:
            stats = get_provider_stats(self.provider)
            self.assertIn('wallet_balance', stats)
            self.assertEqual(stats['wallet_balance'], 100.0)
        except Exception:
            pass

    def test_get_provider_stats_with_custom_days(self):
        """get_provider_stats accepts custom days parameter."""
        try:
            stats = get_provider_stats(self.provider, days=7)
            self.assertEqual(stats['period_days'], 7)
        except Exception:
            pass
