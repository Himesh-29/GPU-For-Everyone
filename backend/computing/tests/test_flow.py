"""
Test Suite: Job Submission Flow
Covers: JobSubmissionView - credit deduction, validation, persistence
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from computing.models import Job, Node
from core.models import User


@pytest.mark.django_db
class TestJobSubmissionAPI:
    """Tests for POST /api/computing/submit-job/"""

    def setup_method(self):
        self.client = APIClient()
        self.consumer = User.objects.create_user(
            username='consumer', password='StrongPass123!',
            wallet_balance=Decimal('10.00')
        )
        self.provider = User.objects.create_user(
            username='provider', password='StrongPass456!', role='PROVIDER',
            wallet_balance=Decimal('0.00')
        )
        self.node = Node.objects.create(
            node_id="node-1", owner=self.provider,
            name="Test GPU", gpu_info={"model": "RTX 4090"}, is_active=True
        )
        # Authenticate as consumer
        self.client.force_authenticate(user=self.consumer)

    # --- Happy Path ---
    def test_submit_job_success(self):
        """POST with a valid prompt returns 201."""
        resp = self.client.post(
            reverse('submit-job'),
            {"prompt": "Hello world"}, format='json',
        )
        assert resp.status_code == 201
        assert resp.data['status'] == 'submitted'
        assert 'job_id' in resp.data

    def test_job_created_in_db(self):
        """Submitted job is persisted with correct fields."""
        self.client.post(
            reverse('submit-job'),
            {"prompt": "Test", "model": "gemma3:270m"}, format='json',
        )
        job = Job.objects.first()
        assert job is not None
        assert job.user == self.consumer
        assert job.task_type == 'inference'
        assert job.input_data['prompt'] == 'Test'
        assert job.input_data['model'] == 'gemma3:270m'
        assert job.status == 'PENDING'

    def test_cost_saved_on_job(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('submit-job'), {"prompt": "X"}, format='json')
        job = Job.objects.first()
        assert job.cost == Decimal('1.00')

    def test_credit_deducted_on_submit(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('submit-job'), {"prompt": "X"}, format='json')
        self.consumer.refresh_from_db()
        assert self.consumer.wallet_balance == Decimal('9.00')

    def test_multiple_jobs_deduct_correctly(self):  # pylint: disable=missing-function-docstring
        for i in range(3):
            self.client.post(reverse('submit-job'), {"prompt": f"Job {i}"}, format='json')
        self.consumer.refresh_from_db()
        assert self.consumer.wallet_balance == Decimal('7.00')
        assert Job.objects.filter(user=self.consumer).count() == 3

    def test_default_model_is_llama(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('submit-job'), {"prompt": "Hello"}, format='json')
        job = Job.objects.first()
        assert job.input_data['model'] == 'llama3.2:latest'

    # --- Validation ---
    def test_missing_prompt_returns_400(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('submit-job'), {"model": "llama3.2:latest"}, format='json')
        assert resp.status_code == 400

    def test_empty_prompt_returns_400(self):  # pylint: disable=missing-function-docstring
        resp = self.client.post(reverse('submit-job'), {"prompt": ""}, format='json')
        assert resp.status_code == 400

    def test_no_job_created_on_validation_error(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('submit-job'), {}, format='json')
        assert Job.objects.count() == 0

    # --- Insufficient Funds ---
    def test_insufficient_funds_returns_402(self):  # pylint: disable=missing-function-docstring
        self.consumer.wallet_balance = Decimal('0.50')
        self.consumer.save()
        resp = self.client.post(reverse('submit-job'), {"prompt": "Test"}, format='json')
        assert resp.status_code == 402

    def test_zero_balance_returns_402(self):  # pylint: disable=missing-function-docstring
        self.consumer.wallet_balance = Decimal('0.00')
        self.consumer.save()
        resp = self.client.post(reverse('submit-job'), {"prompt": "Test"}, format='json')
        assert resp.status_code == 402

    def test_no_deduction_on_insufficient_funds(self):  # pylint: disable=missing-function-docstring
        self.consumer.wallet_balance = Decimal('0.50')
        self.consumer.save()
        self.client.post(reverse('submit-job'), {"prompt": "Test"}, format='json')
        self.consumer.refresh_from_db()
        assert self.consumer.wallet_balance == Decimal('0.50')

    # --- Auth ---
    def test_unauthenticated_returns_401(self):  # pylint: disable=missing-function-docstring
        client = APIClient()  # No auth
        resp = client.post(reverse('submit-job'), {"prompt": "Hello"}, format='json')
        assert resp.status_code == 401

    # --- Job List ---
    def test_job_list_returns_user_jobs(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('submit-job'), {"prompt": "A"}, format='json')
        self.client.post(reverse('submit-job'), {"prompt": "B"}, format='json')
        resp = self.client.get(reverse('job-list'))
        assert resp.status_code == 200
        assert len(resp.data) == 2

    def test_job_list_excludes_other_users(self):  # pylint: disable=missing-function-docstring
        self.client.post(reverse('submit-job'), {"prompt": "Mine"}, format='json')
        # Switch to another user
        other = User.objects.create_user(
            username='other', password='OtherPass1!',
            wallet_balance=Decimal('10.00'),
        )
        self.client.force_authenticate(user=other)
        self.client.post(reverse('submit-job'), {"prompt": "Theirs"}, format='json')
        # Check other user sees only their job
        resp = self.client.get(reverse('job-list'))
        assert len(resp.data) == 1
        assert resp.data[0]['prompt'] == 'Theirs'
