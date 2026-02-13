from celery import shared_task
from .models import Job, Node
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from datetime import timedelta

@shared_task
def find_node_for_job(job_id):
    """
    Finds the best available node for a job.
    This is a simplified matchmaking logic.
    """
    try:
        job = Job.objects.get(id=job_id)
        if job.status != 'PENDING':
            return

        # Simple logic: Find first active node that is NOT busy
        # In real world: check GPU specs, memory, etc.
        # Check active nodes with heartbeat in last 30s
        cutoff = timezone.now() - timedelta(seconds=30)
        
        # We need to find a node that is NOT owned by the job submitter? 
        # Or allow self-use? Let's allow any node for now.
        node = Node.objects.filter(is_active=True, last_heartbeat__gte=cutoff).first()
        
        if node:
            job.node = node
            job.status = 'RUNNING'
            job.save()
            
            # Send Job to Node via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{node.owner.id}_nodes",
                {
                    "type": "send_job",
                    "job": {
                        "id": job.id,
                        "task_type": job.task_type,
                        "input_data": job.input_data
                    }
                }
            )
            return f"Assigned Job {job.id} to Node {node.id}"
        else:
            # Retry later?
            return "No nodes available"

    except Job.DoesNotExist:
        return "Job not found"
