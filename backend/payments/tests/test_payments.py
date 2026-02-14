"""
Test Suite: Payment System
Covers: Wallet balance, deposit, credit transfer, mock webhook
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import User
from payments.models import CreditLog, Transaction
from payments.services import CreditService


@pytest.mark.django_db
class TestCreditService:
    """Tests for CreditService business logic."""

    def setup_method(self):
        self.sender = User.objects.create_user(
            username='sender', password='p',
            wallet_balance=Decimal('50.00')
        )
        self.receiver = User.objects.create_user(
            username='receiver', password='p',
            wallet_balance=Decimal('10.00')
        )

    def test_transfer_credits_success(self):  # pylint: disable=missing-function-docstring
        CreditService.transfer_credits(self.sender, self.receiver, Decimal('20.00'), job_id=1)
        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        assert self.sender.wallet_balance == Decimal('30.00')
        assert self.receiver.wallet_balance == Decimal('30.00')

    def test_transfer_creates_credit_logs(self):  # pylint: disable=missing-function-docstring
        CreditService.transfer_credits(self.sender, self.receiver, Decimal('5.00'), job_id=42)
        logs = CreditLog.objects.all()
        assert logs.count() == 2
        sender_log = CreditLog.objects.filter(user=self.sender).first()
        receiver_log = CreditLog.objects.filter(user=self.receiver).first()
        assert sender_log.amount == Decimal('-5.00')
        assert receiver_log.amount == Decimal('5.00')
        assert 'Job 42' in sender_log.description

    def test_transfer_insufficient_funds_raises(self):  # pylint: disable=missing-function-docstring
        with pytest.raises(ValueError, match="Insufficient funds"):
            CreditService.transfer_credits(self.sender, self.receiver, Decimal('999.00'))

    def test_transfer_insufficient_funds_no_change(self):  # pylint: disable=missing-function-docstring
        try:
            CreditService.transfer_credits(self.sender, self.receiver, Decimal('999.00'))
        except ValueError:
            pass
        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        assert self.sender.wallet_balance == Decimal('50.00')
        assert self.receiver.wallet_balance == Decimal('10.00')


@pytest.mark.django_db
class TestDepositWebhookFlow:
    """Tests for deposit transaction + mock webhook processing."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='depositor', password='p',
            wallet_balance=Decimal('10.00')
        )

    def test_process_deposit_adds_to_wallet(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('50.00'),
            type='DEPOSIT', status='PENDING'
        )
        result = CreditService.process_transaction(txn.id)
        assert result is True
        self.user.refresh_from_db()
        assert self.user.wallet_balance == Decimal('60.00')

    def test_process_deposit_changes_status(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('25.00'),
            type='DEPOSIT', status='PENDING'
        )
        CreditService.process_transaction(txn.id)
        txn.refresh_from_db()
        assert txn.status == 'SUCCESS'

    def test_process_already_completed(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('25.00'),
            type='DEPOSIT', status='SUCCESS'
        )
        result = CreditService.process_transaction(txn.id)
        assert result is False

    def test_withdrawal_insufficient_fails(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('999.00'),
            type='WITHDRAWAL', status='PENDING'
        )
        result = CreditService.process_transaction(txn.id)
        assert result is False
        txn.refresh_from_db()
        assert txn.status == 'FAILED'

    def test_mock_webhook_endpoint(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('10.00'),
            type='DEPOSIT', status='PENDING'
        )
        url = reverse('mock-webhook', kwargs={'transaction_id': txn.id})
        resp = self.client.post(url)
        assert resp.status_code == 200
        self.user.refresh_from_db()
        assert self.user.wallet_balance == Decimal('20.00')

    def test_mock_webhook_nonexistent_transaction(self):  # pylint: disable=missing-function-docstring
        url = reverse('mock-webhook', kwargs={'transaction_id': 99999})
        resp = self.client.post(url)
        assert resp.status_code == 400


@pytest.mark.django_db
class TestWithdrawalFlow:
    """Tests for withdrawal processing."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username='withdrawer', password='p',
            wallet_balance=Decimal('100.00')
        )

    def test_process_withdrawal_success(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('30.00'),
            type='WITHDRAWAL', status='PENDING'
        )
        result = CreditService.process_transaction(txn.id)
        assert result is True
        self.user.refresh_from_db()
        assert self.user.wallet_balance == Decimal('70.00')
        txn.refresh_from_db()
        assert txn.status == 'SUCCESS'

    def test_process_withdrawal_creates_log(self):  # pylint: disable=missing-function-docstring
        txn = Transaction.objects.create(
            user=self.user, amount=Decimal('20.00'),
            type='WITHDRAWAL', status='PENDING'
        )
        CreditService.process_transaction(txn.id)
        log = CreditLog.objects.filter(user=self.user, amount__lt=0).first()
        assert log is not None
        assert log.amount == Decimal('-20.00')
        assert 'Withdrawal' in log.description

    def test_process_nonexistent_transaction(self):  # pylint: disable=missing-function-docstring
        result = CreditService.process_transaction(99999)
        assert result is False


@pytest.mark.django_db
class TestWalletBalanceView:
    """Tests for the WalletBalanceView."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='walletuser', password='p',
            wallet_balance=Decimal('75.00')
        )

    def test_unauthenticated_returns_401(self):  # pylint: disable=missing-function-docstring
        url = reverse('wallet')
        resp = self.client.get(url)
        assert resp.status_code == 401

    def test_authenticated_returns_balance(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.user)
        url = reverse('wallet')
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert str(resp.data['balance']) == '75.00'
        assert 'logs' in resp.data

    def test_balance_with_credit_logs(self):  # pylint: disable=missing-function-docstring
        CreditLog.objects.create(
            user=self.user, amount=Decimal('10.00'),
            description='Test credit'
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('wallet')
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert len(resp.data['logs']) == 1


@pytest.mark.django_db
class TestDepositView:
    """Tests for the DepositView."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='depositer', password='p',
            wallet_balance=Decimal('50.00')
        )

    def test_create_deposit(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.user)
        url = reverse('deposit')
        resp = self.client.post(url, {
            'amount': '25.00', 'gateway_id': 'stripe_test_123',
            'type': 'DEPOSIT',
        })
        assert resp.status_code == 201
        txn = Transaction.objects.get(user=self.user)
        assert txn.type == 'DEPOSIT'
        assert txn.status == 'PENDING'
        assert txn.amount == Decimal('25.00')

    def test_create_deposit_unauthenticated(self):  # pylint: disable=missing-function-docstring
        url = reverse('deposit')
        resp = self.client.post(url, {'amount': '25.00'})
        assert resp.status_code == 401
