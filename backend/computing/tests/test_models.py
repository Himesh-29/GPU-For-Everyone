"""
Test Suite: Model Integrity
Covers: __str__ representations, defaults, constraints
"""
from decimal import Decimal

import pytest

from computing.models import Job, Node
from core.models import User
from payments.models import CreditLog, Transaction


@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""
    def test_str_representation(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='alice', password='p')
        assert str(user) == 'alice'

    def test_default_role_is_user(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='bob', password='p')
        assert user.role == 'USER'

    def test_default_wallet_balance_is_100(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='carol', password='p')
        assert user.wallet_balance == Decimal('100.00')

    def test_wallet_is_decimal_type(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='dave', password='p')
        assert isinstance(user.wallet_balance, Decimal)

    def test_provider_role(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='eve', password='p', role='PROVIDER')
        assert user.role == 'PROVIDER'


@pytest.mark.django_db
class TestNodeModel:
    """Tests for the Node model."""
    def test_str_representation(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='provider', password='p')
        node = Node.objects.create(
            node_id='n1', owner=user, name='My Node',
            gpu_info={'gpu': 'RTX 4090'}
        )
        assert str(node) == "My Node (n1)"

    def test_default_inactive(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='p2', password='p')
        node = Node.objects.create(node_id='n2', owner=user, name='Node2', gpu_info={})
        assert node.is_active is False

    def test_node_id_unique(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='p3', password='p')
        Node.objects.create(node_id='unique1', owner=user, name='A', gpu_info={})
        with pytest.raises(Exception):
            Node.objects.create(node_id='unique1', owner=user, name='B', gpu_info={})


@pytest.mark.django_db
class TestJobModel:
    """Tests for the Job model."""

    def test_str_representation(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='u1', password='p')
        job = Job.objects.create(
            user=user, task_type='inference',
            input_data={"prompt": "Hi"}, status='PENDING'
        )
        assert str(job) == f"Job {job.id} - PENDING"

    def test_default_status_pending(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='u2', password='p')
        job = Job.objects.create(user=user, task_type='inference', input_data={})
        assert job.status == 'PENDING'

    def test_result_null_by_default(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='u3', password='p')
        job = Job.objects.create(user=user, task_type='inference', input_data={})
        assert job.result is None

    def test_node_nullable(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='u4', password='p')
        job = Job.objects.create(user=user, task_type='inference', input_data={})
        assert job.node is None


@pytest.mark.django_db
class TestTransactionModel:
    """Tests for the Transaction model."""

    def test_str_representation(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='t1', password='p')
        txn = Transaction.objects.create(
            user=user, amount=Decimal('25.00'), type='DEPOSIT'
        )
        assert str(txn) == "DEPOSIT - 25.00 - PENDING"

    def test_default_status_pending(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='t2', password='p')
        txn = Transaction.objects.create(
            user=user, amount=Decimal('10.00'), type='WITHDRAWAL'
        )
        assert txn.status == 'PENDING'


@pytest.mark.django_db
class TestCreditLogModel:
    """Tests for the CreditLog model."""

    def test_credit_log_creation(self):  # pylint: disable=missing-function-docstring
        user = User.objects.create_user(username='cl1', password='p')
        log = CreditLog.objects.create(
            user=user, amount=Decimal('5.00'), description='Test deposit'
        )
        assert log.amount == Decimal('5.00')
        assert log.description == 'Test deposit'
