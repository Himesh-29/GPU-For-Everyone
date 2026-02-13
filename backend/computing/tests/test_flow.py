"""
Test Suite: Job Submission Flow
Covers: JobSubmissionView - credit deduction, validation, persistence
"""
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from core.models import User
from computing.models import Job, Node
from decimal import Decimal


@pytest.mark.django_db
class TestJobSubmissionAPI:
    """Tests for POST /api/computing/submit-job/"""

    def setup_method(self):
        self.client = APIClient()
        self.consumer = User.objects.create_user(
            username='consumer', password='pass123',
            wallet_balance=Decimal('10.00')
        )
        self.provider = User.objects.create_user(
            username='provider', password='pass123', role='PROVIDER',
            wallet_balance=Decimal('0.00')
        )
        self.node = Node.objects.create(
            node_id="node-1", owner=self.provider,
            name="Test GPU", gpu_info={"model": "RTX 4090"}, is_active=True
        )

    # --- Happy Path ---
    def test_submit_job_success(self):
        """Authenticated user with funds can submit a job."""
        self.client.force_authenticate(user=self.consumer)
        url = reverse('submit-job')
        resp = self.client.post(url, {"prompt": "Hello world", "model": "llama3.2:latest"}, format='json')
        assert resp.status_code == 201
        assert resp.data['status'] == 'submitted'
        assert 'job_id' in resp.data

    def test_job_created_in_db(self):
        """Job record is persisted with correct data."""
        self.client.force_authenticate(user=self.consumer)
        self.client.post(reverse('submit-job'), {"prompt": "Test", "model": "gemma3:270m"}, format='json')
        job = Job.objects.first()
        assert job is not None
        assert job.user == self.consumer
        assert job.task_type == 'inference'
        assert job.input_data['prompt'] == 'Test'
        assert job.input_data['model'] == 'gemma3:270m'
        assert job.status == 'PENDING'

    def test_credit_deducted_on_submit(self):
        """Wallet balance decreases by 1.00 per job."""
        self.client.force_authenticate(user=self.consumer)
        self.client.post(reverse('submit-job'), {"prompt": "X"}, format='json')
        self.consumer.refresh_from_db()
        assert self.consumer.wallet_balance == Decimal('9.00')

    def test_multiple_jobs_deduct_correctly(self):
        """Submitting 3 jobs deducts 3.00 credits."""
        self.client.force_authenticate(user=self.consumer)
        for i in range(3):
            self.client.post(reverse('submit-job'), {"prompt": f"Job {i}"}, format='json')
        self.consumer.refresh_from_db()
        assert self.consumer.wallet_balance == Decimal('7.00')
        assert Job.objects.filter(user=self.consumer).count() == 3

    def test_default_model_is_llama(self):
        """If no model specified, defaults to llama3.2:latest."""
        self.client.force_authenticate(user=self.consumer)
        self.client.post(reverse('submit-job'), {"prompt": "Hello"}, format='json')
        job = Job.objects.first()
        assert job.input_data['model'] == 'llama3.2:latest'

    # --- Validation ---
    def test_missing_prompt_returns_400(self):
        """Prompt is required."""
        self.client.force_authenticate(user=self.consumer)
        resp = self.client.post(reverse('submit-job'), {"model": "llama3.2:latest"}, format='json')
        assert resp.status_code == 400
        assert 'error' in resp.data

    def test_empty_prompt_returns_400(self):
        """Empty string prompt is rejected."""
        self.client.force_authenticate(user=self.consumer)
        resp = self.client.post(reverse('submit-job'), {"prompt": ""}, format='json')
        assert resp.status_code == 400

    def test_no_job_created_on_validation_error(self):
        """No DB record if validation fails."""
        self.client.force_authenticate(user=self.consumer)
        self.client.post(reverse('submit-job'), {}, format='json')
        assert Job.objects.count() == 0

    # --- Insufficient Funds ---
    def test_insufficient_funds_returns_402(self):
        """User with < 1.00 credits cannot submit."""
        self.consumer.wallet_balance = Decimal('0.50')
        self.consumer.save()
        self.client.force_authenticate(user=self.consumer)
        resp = self.client.post(reverse('submit-job'), {"prompt": "Test"}, format='json')
        assert resp.status_code == 402

    def test_zero_balance_returns_402(self):
        """User with 0 credits cannot submit."""
        self.consumer.wallet_balance = Decimal('0.00')
        self.consumer.save()
        self.client.force_authenticate(user=self.consumer)
        resp = self.client.post(reverse('submit-job'), {"prompt": "Test"}, format='json')
        assert resp.status_code == 402
        assert Job.objects.count() == 0

    def test_no_deduction_on_insufficient_funds(self):
        """Balance unchanged if submission rejected."""
        self.consumer.wallet_balance = Decimal('0.50')
        self.consumer.save()
        self.client.force_authenticate(user=self.consumer)
        self.client.post(reverse('submit-job'), {"prompt": "Test"}, format='json')
        self.consumer.refresh_from_db()
        assert self.consumer.wallet_balance == Decimal('0.50')

    # --- Unauthenticated Access ---
    def test_unauthenticated_creates_mock_user(self):
        """Unauthenticated requests create a test_consumer user (PoC behavior)."""
        resp = self.client.post(reverse('submit-job'), {"prompt": "Anon test"}, format='json')
        # The view creates a test_consumer user for unauthenticated requests
        assert resp.status_code == 201
        assert User.objects.filter(username='test_consumer').exists()
