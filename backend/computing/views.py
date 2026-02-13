from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Job, Node
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal


class JobSubmissionView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

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
            status="PENDING",
            cost=JOB_COST,
        )

        # 2. Dispatch to all connected GPU provider nodes
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
        if job.user != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "id": job.id,
            "status": job.status,
            "result": job.result,
            "prompt": job.input_data.get("prompt"),
            "model": job.input_data.get("model"),
            "cost": str(job.cost) if job.cost else None,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        })


class JobListView(views.APIView):
    """List all jobs for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.filter(user=request.user).order_by('-created_at')
        data = [{
            "id": j.id,
            "status": j.status,
            "prompt": j.input_data.get("prompt", "")[:80],
            "model": j.input_data.get("model", ""),
            "cost": str(j.cost) if j.cost else None,
            "result": j.result,
            "created_at": j.created_at,
            "completed_at": j.completed_at,
        } for j in jobs]
        return Response(data)
