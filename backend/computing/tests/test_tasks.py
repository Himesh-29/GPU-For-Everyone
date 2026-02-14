"""Tests for Celery tasks in the computing module."""
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from computing.models import Job, Node
from computing.tasks import find_node_for_job

User = get_user_model()


class FindNodeForJobTests(TestCase):
    """Tests for the find_node_for_job Celery task."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="taskuser", password="p",
            wallet_balance=Decimal("100.00"),
        )
        self.node = Node.objects.create(
            owner=self.user,
            node_id="task-node-1",
            name="Task Node",
            gpu_info={"models": ["llama2"]},
            is_active=True,
            last_heartbeat=timezone.now(),
        )

    def test_assigns_pending_job_to_node(self):
        """find_node_for_job assigns a PENDING job to an active node."""
        job = Job.objects.create(
            user=self.user, task_type="inference",
            input_data={"prompt": "hello"}, status="PENDING",
        )
        with patch("computing.tasks.get_channel_layer") as mock_cl:
            mock_layer = MagicMock()
            mock_layer.group_send = AsyncMock()
            mock_cl.return_value = mock_layer
            result = find_node_for_job(job.id)

        job.refresh_from_db()
        self.assertEqual(job.status, "RUNNING")
        self.assertEqual(job.node, self.node)
        self.assertIn("Assigned", result)

    def test_skips_non_pending_job(self):
        """find_node_for_job returns None for non-PENDING job."""
        job = Job.objects.create(
            user=self.user, task_type="inference",
            input_data={"prompt": "hello"}, status="RUNNING",
        )
        result = find_node_for_job(job.id)
        self.assertIsNone(result)

    def test_no_available_nodes(self):
        """find_node_for_job returns message when no nodes available."""
        self.node.is_active = False
        self.node.save()
        job = Job.objects.create(
            user=self.user, task_type="inference",
            input_data={"prompt": "hello"}, status="PENDING",
        )
        result = find_node_for_job(job.id)
        self.assertEqual(result, "No nodes available")

    def test_nonexistent_job(self):
        """find_node_for_job returns message for nonexistent job."""
        result = find_node_for_job(99999)
        self.assertEqual(result, "Job not found")

    def test_ignores_stale_node(self):
        """find_node_for_job ignores nodes with old heartbeat."""
        from datetime import timedelta
        # Make the only node's heartbeat stale
        Node.objects.all().update(
            last_heartbeat=timezone.now() - timedelta(minutes=5),
        )
        job = Job.objects.create(
            user=self.user, task_type="inference",
            input_data={"prompt": "hello"}, status="PENDING",
        )
        result = find_node_for_job(job.id)
        self.assertEqual(result, "No nodes available")
        job.refresh_from_db()
        self.assertEqual(job.status, "PENDING")
