"""Tests for computing utilities."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from payments.models import CreditLog
from ..models import Job, Node
from ..utils import get_provider_stats

User = get_user_model()


class GetProviderStatsTests(TestCase):
    """Test provider stats utility function."""

    def setUp(self):
        """Set up test data."""
        self.provider = User.objects.create_user(
            username='provider', password='pass',
            wallet_balance=Decimal('100.00'),
        )
        self.consumer = User.objects.create_user(
            username='consumer', password='pass',
        )
        self.node = Node.objects.create(
            owner=self.provider,
            node_id='node-1',
            name='Node 1',
            gpu_info={'gpu_model': 'RTX 4090', 'count': 1},
            is_active=True,
        )

    def test_get_provider_stats_returns_dict(self):
        """get_provider_stats returns a dictionary."""
        stats = get_provider_stats(self.provider)
        self.assertIsInstance(stats, dict)

    def test_get_provider_stats_has_provider_data(self):
        """get_provider_stats includes provider data."""
        stats = get_provider_stats(self.provider)
        self.assertIn('active_nodes', stats['provider'])
        self.assertIn('total_earnings', stats['provider'])

    def test_get_provider_stats_has_consumer_data(self):
        """get_provider_stats includes consumer data."""
        stats = get_provider_stats(self.provider)
        self.assertIn('total_spent', stats['consumer'])
        self.assertIn('total_jobs', stats['consumer'])

    def test_get_provider_stats_has_wallet_balance(self):
        """get_provider_stats includes wallet balance."""
        stats = get_provider_stats(self.provider)
        self.assertIn('wallet_balance', stats)
        self.assertEqual(stats['wallet_balance'], 100.0)

    def test_get_provider_stats_with_custom_days(self):
        """get_provider_stats accepts custom days parameter."""
        stats = get_provider_stats(self.provider, days=7)
        self.assertEqual(stats['period_days'], 7)

    def test_earnings_by_day(self):
        """get_provider_stats includes earnings_by_day data."""
        CreditLog.objects.create(
            user=self.provider, amount=Decimal('5.00'),
            description='Earned: Job #1 completed (model: llama2)',
        )
        CreditLog.objects.create(
            user=self.provider, amount=Decimal('3.00'),
            description='Earned: Job #2 completed (model: mistral)',
        )
        stats = get_provider_stats(self.provider, days=30)
        ebd = stats['provider']['earnings_by_day']
        self.assertIsInstance(ebd, list)
        self.assertGreater(len(ebd), 0)
        entry = ebd[0]
        self.assertIn('date', entry)
        self.assertIn('earned', entry)
        self.assertIn('jobs', entry)
        self.assertIsInstance(entry['date'], str)
        self.assertIsInstance(entry['earned'], float)

    def test_model_breakdown_with_completed_jobs(self):
        """get_provider_stats includes model breakdown for served jobs."""
        Job.objects.create(
            user=self.consumer, node=self.node,
            task_type='inference',
            input_data={'model': 'llama2', 'prompt': 'hi'},
            status='COMPLETED',
            completed_at=timezone.now(),
        )
        Job.objects.create(
            user=self.consumer, node=self.node,
            task_type='inference',
            input_data={'model': 'llama2', 'prompt': 'hello'},
            status='COMPLETED',
            completed_at=timezone.now(),
        )
        stats = get_provider_stats(self.provider, days=30)
        breakdown = stats['provider']['model_breakdown']
        self.assertIsInstance(breakdown, list)
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['model'], 'llama2')
        self.assertEqual(breakdown[0]['jobs'], 2)

    def test_consumer_jobs_in_stats(self):
        """get_provider_stats includes jobs submitted by user."""
        Job.objects.create(
            user=self.provider, node=self.node,
            task_type='inference',
            input_data={'model': 'llama2', 'prompt': 'testing'},
            status='PENDING',
        )
        stats = get_provider_stats(self.provider, days=30)
        self.assertEqual(stats['consumer']['total_jobs'], 1)
        self.assertEqual(len(stats['consumer']['jobs']), 1)
        self.assertEqual(stats['consumer']['jobs'][0]['prompt'], 'testing')

    def test_consumer_jobs_non_dict_input(self):
        """get_provider_stats handles non-dict input_data for consumer jobs."""
        Job.objects.create(
            user=self.provider, node=self.node,
            task_type='inference',
            input_data='raw string prompt',
            status='PENDING',
        )
        stats = get_provider_stats(self.provider, days=30)
        self.assertEqual(stats['consumer']['jobs'][0]['prompt'], 'raw string prompt')

    def test_model_breakdown_unknown_model(self):
        """Model breakdown uses 'unknown' when input_data has no model key."""
        Job.objects.create(
            user=self.consumer, node=self.node,
            task_type='inference',
            input_data={'prompt': 'no model key'},
            status='COMPLETED',
            completed_at=timezone.now(),
        )
        stats = get_provider_stats(self.provider, days=30)
        breakdown = stats['provider']['model_breakdown']
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['model'], 'unknown')

    def test_model_breakdown_non_dict_input(self):
        """Model breakdown uses 'unknown' for non-dict input_data."""
        Job.objects.create(
            user=self.consumer, node=self.node,
            task_type='inference',
            input_data='just a string',
            status='COMPLETED',
            completed_at=timezone.now(),
        )
        stats = get_provider_stats(self.provider, days=30)
        breakdown = stats['provider']['model_breakdown']
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['model'], 'unknown')

    def test_transactions_in_stats(self):
        """get_provider_stats includes recent transactions."""
        CreditLog.objects.create(
            user=self.provider, amount=Decimal('10.00'),
            description='Earned: Job #1 completed (model: llama2)',
        )
        CreditLog.objects.create(
            user=self.provider, amount=Decimal('-5.00'),
            description='Spent: Job #2 (model: llama2)',
        )
        stats = get_provider_stats(self.provider, days=30)
        txns = stats['transactions']
        self.assertEqual(len(txns), 2)
        types = {t['type'] for t in txns}
        self.assertIn('earning', types)
        self.assertIn('spending', types)

    def test_total_spent(self):
        """get_provider_stats calculates total spent correctly."""
        CreditLog.objects.create(
            user=self.provider, amount=Decimal('-10.00'),
            description='Spent: Job #1',
        )
        CreditLog.objects.create(
            user=self.provider, amount=Decimal('-5.00'),
            description='Spent: Job #2',
        )
        stats = get_provider_stats(self.provider, days=30)
        self.assertEqual(stats['consumer']['total_spent'], 15.0)
