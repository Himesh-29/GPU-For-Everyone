import pytest
from django.contrib.auth import get_user_model
from computing.models import Job, Node
from computing.tasks import find_node_for_job
from django.utils import timezone

User = get_user_model()

@pytest.mark.django_db
class TestComputingSystem:
    def setup_method(self):
        self.user = User.objects.create_user(username='consumer', password='password')
        self.provider = User.objects.create_user(username='provider', password='password')
        self.node = Node.objects.create(
            owner=self.provider,
            node_id='gpu-worker-1',
            name='My RTX 4090',
            is_active=True
        )

    def test_job_matchmaking(self):
        # 1. Create a Job
        job = Job.objects.create(
            user=self.user,
            task_type='inference',
            input_data={'model': 'llama-3'},
            status='PENDING'
        )
        
        # 2. Run the Task (Synchronously for test)
        result = find_node_for_job(job.id)
        
        # 3. Assertions
        job.refresh_from_db()
        assert job.status == 'RUNNING'
        assert job.node == self.node
        assert result == f"Assigned Job {job.id} to Node {self.node.id}"

    def test_no_nodes_available(self):
        # Make node inactive
        self.node.is_active = False
        self.node.save()
        
        job = Job.objects.create(
            user=self.user,
            task_type='training',
            input_data={},
            status='PENDING'
        )
        
        result = find_node_for_job(job.id)
        
        job.refresh_from_db()
        assert job.status == 'PENDING'
        assert result == "No nodes available"
