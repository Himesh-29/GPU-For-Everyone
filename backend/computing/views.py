from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Job, Node
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal

class JobSubmissionView(views.APIView):
    # permission_classes = [IsAuthenticated] # Disable for initial testing if needed

    def post(self, request):
        user = request.user
        # Mock user for testing if not authenticated
        if not user.is_authenticated:
            from core.models import User
            user, _ = User.objects.get_or_create(username="test_consumer", defaults={"email": "test@example.com"})
        
        prompt = request.data.get("prompt")
        model = request.data.get("model", "llama3.2:latest")
        
        if not prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check Balance (Simple PoC: 1 credit per job)
        JOB_COST = Decimal('1.00')
        if user.wallet_balance < JOB_COST:
            return Response({"error": "Insufficient funds"}, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        user.wallet_balance -= JOB_COST
        user.save()

        # 1. Create Job in DB
        job = Job.objects.create(
            user=user,
            task_type="inference",
            input_data={"prompt": prompt, "model": model},
            status="PENDING"
        )

        # 2. Dispatch to Agent (Mock: Broadcast to all for now, or pick first active)
        # For PoC, we just broadcast to the 'computing' group if we had one, 
        # or we need to find the specific channel name of a connected node.
        # Since we didn't implement Group add in consumers.py yet, let's fix that first in consumers.py
        # But for now, let's assume we broadcast to a group named 'gpu_nodes'
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "gpu_nodes", 
            {
                "type": "job_dispatch",
                "job_data": {
                    "task_id": job.id,
                    "model": model,
                    "prompt": prompt
                }
            }
        )

        return Response({"status": "submitted", "job_id": job.id}, status=status.HTTP_201_CREATED)

class JobDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        # Ensure user can only see their own jobs
        if job.user != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            "id": job.id,
            "status": job.status,
            "result": job.result,
            "prompt": job.input_data.get("prompt"),
            "cost": job.cost,
            "created_at": job.created_at
        })
