"""
Test Suite: Job Lifecycle & Security
Covers: Job status transitions, result storage, job detail endpoint, isolation
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from computing.models import Job
from core.models import User


@pytest.mark.django_db
class TestJobLifecycle:
    """Tests for job status transitions (Model-level)."""

    def setup_method(self):
        """Create a user and a pending job for each test."""
        self.user = User.objects.create_user(
            username='owner', password='pass123',
            wallet_balance=Decimal('50.00')
        )
        self.job = Job.objects.create(
            user=self.user, task_type='inference',
            input_data={"prompt": "Test", "model": "llama3.2"},
            status='PENDING', cost=Decimal('1.00')
        )

    def test_pending_to_running(self):  # pylint: disable=missing-function-docstring
        self.job.status = 'RUNNING'
        self.job.save()
        self.job.refresh_from_db()
        assert self.job.status == 'RUNNING'

    def test_running_to_completed(self):  # pylint: disable=missing-function-docstring
        self.job.status = 'COMPLETED'
        self.job.result = {"output": "The answer is 42."}
        self.job.save()
        self.job.refresh_from_db()
        assert self.job.status == 'COMPLETED'
        assert self.job.result['output'] == "The answer is 42."

    def test_pending_to_failed(self):  # pylint: disable=missing-function-docstring
        self.job.status = 'FAILED'
        self.job.result = {"error": "Ollama timeout"}
        self.job.save()
        self.job.refresh_from_db()
        assert self.job.status == 'FAILED'

    def test_completed_at_is_null_initially(self):  # pylint: disable=missing-function-docstring
        assert self.job.completed_at is None

    def test_created_at_is_set(self):  # pylint: disable=missing-function-docstring
        assert self.job.created_at is not None


@pytest.mark.django_db
class TestJobDetailAPI:
    """Tests for GET /api/computing/jobs/<id>/"""

    def setup_method(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='owner', password='pass123',
            wallet_balance=Decimal('50.00')
        )
        self.stranger = User.objects.create_user(
            username='stranger', password='pass123',
            wallet_balance=Decimal('50.00')
        )
        self.job = Job.objects.create(
            user=self.owner, task_type='inference',
            input_data={"prompt": "Secret prompt", "model": "llama3.2"},
            status='PENDING', cost=Decimal('1.00')
        )

    def test_owner_can_view_job(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.owner)
        url = reverse('job-detail', kwargs={'job_id': self.job.id})
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data['prompt'] == "Secret prompt"

    def test_stranger_cannot_view_job(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.stranger)
        url = reverse('job-detail', kwargs={'job_id': self.job.id})
        resp = self.client.get(url)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_view_job(self):  # pylint: disable=missing-function-docstring
        url = reverse('job-detail', kwargs={'job_id': self.job.id})
        resp = self.client.get(url)
        assert resp.status_code == 401

    def test_nonexistent_job_returns_404(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.owner)
        url = reverse('job-detail', kwargs={'job_id': 99999})
        resp = self.client.get(url)
        assert resp.status_code == 404

    def test_job_detail_includes_all_fields(self):  # pylint: disable=missing-function-docstring
        self.client.force_authenticate(user=self.owner)
        url = reverse('job-detail', kwargs={'job_id': self.job.id})
        resp = self.client.get(url)
        assert 'id' in resp.data
        assert 'status' in resp.data
        assert 'result' in resp.data
        assert 'prompt' in resp.data
        assert 'cost' in resp.data
        assert 'created_at' in resp.data
