import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from .models import Node, Job

logger = logging.getLogger(__name__)

class GPUConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # TODO: Real Auth
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
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")
        
        if msg_type == "register":
            self.node_id = data.get("node_id")
            gpu_info = data.get("gpu_info")
            logger.info(f"Registering Node: {self.node_id} with info {gpu_info}")
            
            # Save to DB (Simplified for async)
            # In production, use sync_to_async or database_sync_to_async
            # node, created = await Node.objects.aget_or_create(node_id=self.node_id)
            # node.gpu_info = gpu_info
            # node.is_active = True
            # await node.asave()
            
            await self.send(json.dumps({"type": "registered", "status": "ok"}))
            
        elif msg_type == "job_result":
            result = data.get("result")
            logger.info(f"Job Result Received: {result}")
            # Update Job status in DB
            
        elif msg_type == "pong":
            pass
            
    async def job_dispatch(self, event):
        """
        Handler for sending a job to this consumer.
        Triggered by channel_layer.group_send
        """
        job_data = event["job_data"]
        await self.send(json.dumps({
            "type": "job_dispatch",
            "job_data": job_data
        }))
