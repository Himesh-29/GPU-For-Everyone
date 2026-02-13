import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


class GPUConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.node_id = "unknown"
        self.group_name = "gpu_nodes"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("WebSocket Connected")

    async def disconnect(self, close_code):
        logger.info(f"WebSocket Disconnected: {close_code}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        # Mark node inactive
        if self.node_id != "unknown":
            await self._mark_node_inactive(self.node_id)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "register":
            self.node_id = data.get("node_id")
            gpu_info = data.get("gpu_info")
            logger.info(f"Registering Node: {self.node_id} with info {gpu_info}")

            await self._register_node(self.node_id, gpu_info)
            await self.send(json.dumps({"type": "registered", "status": "ok"}))

        elif msg_type == "job_result":
            result = data.get("result", {})
            task_id = result.get("task_id")
            status = result.get("status", "failed")
            response_text = result.get("response", "")
            error = result.get("error", "")

            logger.info(f"Job Result Received for Task {task_id}: {status}")

            if task_id:
                if status == "success":
                    await self._complete_job(task_id, {"output": response_text})
                else:
                    await self._fail_job(task_id, {"error": error})

        elif msg_type == "pong":
            pass

    async def job_dispatch(self, event):
        """Handler for sending a job to this consumer."""
        job_data = event["job_data"]
        await self.send(json.dumps({
            "type": "job_dispatch",
            "job_data": job_data
        }))

    # --- DB Operations (sync_to_async wrappers) ---

    @database_sync_to_async
    def _register_node(self, node_id, gpu_info):
        from .models import Node
        from core.models import User
        # Use a system provider user for unauth'd agents
        owner, _ = User.objects.get_or_create(
            username="system_provider",
            defaults={"email": "provider@system.local", "role": "PROVIDER"}
        )
        node, created = Node.objects.update_or_create(
            node_id=node_id,
            defaults={
                "owner": owner,
                "name": f"Node-{node_id}",
                "gpu_info": gpu_info or {},
                "is_active": True,
            }
        )
        action = "Created" if created else "Updated"
        logger.info(f"{action} Node: {node}")

    @database_sync_to_async
    def _mark_node_inactive(self, node_id):
        from .models import Node
        Node.objects.filter(node_id=node_id).update(is_active=False)
        logger.info(f"Node {node_id} marked inactive")

    @database_sync_to_async
    def _complete_job(self, task_id, result_data):
        from .models import Job
        try:
            job = Job.objects.get(id=task_id)
            job.status = "COMPLETED"
            job.result = result_data
            job.completed_at = timezone.now()
            job.cost = Decimal("1.00")
            job.save()
            logger.info(f"Job {task_id} completed successfully")
        except Job.DoesNotExist:
            logger.error(f"Job {task_id} not found")

    @database_sync_to_async
    def _fail_job(self, task_id, error_data):
        from .models import Job
        try:
            job = Job.objects.get(id=task_id)
            job.status = "FAILED"
            job.result = error_data
            job.completed_at = timezone.now()
            job.save()
            logger.error(f"Job {task_id} failed: {error_data}")
        except Job.DoesNotExist:
            logger.error(f"Job {task_id} not found")
