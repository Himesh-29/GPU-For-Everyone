from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
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

        job = Job.objects.create(
            user=user,
            task_type="inference",
            input_data={"prompt": prompt, "model": model},
            status="PENDING",
            cost=JOB_COST,
        )

        # Dispatch to all connected GPU provider nodes
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


class AvailableModelsView(views.APIView):
    """Returns models available across all active nodes.
    
    Public endpoint — consumers can browse what's available before signing up.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        active_nodes = Node.objects.filter(is_active=True)
        model_map = {}  # model_name -> { providers: int, node_ids: [] }

        for node in active_nodes:
            models = node.gpu_info.get("models", [])
            for m in models:
                if m not in model_map:
                    model_map[m] = {
                        "name": m,
                        "providers": 0,
                        "nodes": [],
                    }
                model_map[m]["providers"] += 1
                model_map[m]["nodes"].append(node.node_id)

        models_list = sorted(model_map.values(), key=lambda x: -x["providers"])
        return Response({
            "models": models_list,
            "total_nodes": active_nodes.count(),
        })


class NetworkStatsView(views.APIView):
    """Public endpoint for network statistics."""
    permission_classes = [AllowAny]

    def get(self, request):
        active_nodes = Node.objects.filter(is_active=True).count()
        total_jobs = Job.objects.count()
        completed_jobs = Job.objects.filter(status="COMPLETED").count()

        # Collect unique models
        all_models = set()
        for node in Node.objects.filter(is_active=True):
            for m in node.gpu_info.get("models", []):
                all_models.add(m)

        return Response({
            "active_nodes": active_nodes,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "available_models": len(all_models),
        })


class ProviderStatsView(views.APIView):
    """Authenticated endpoint returning comprehensive provider metrics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from payments.models import CreditLog
        from django.db.models import Sum, Count, Q
        from django.db.models.functions import TruncDate
        import datetime

        user = request.user
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - datetime.timedelta(days=days)

        # --- Provider Nodes ---
        my_nodes = Node.objects.filter(owner=user)
        active_nodes = my_nodes.filter(is_active=True)

        # --- Jobs Served (jobs completed on my nodes) ---
        jobs_served = Job.objects.filter(
            node__owner=user,
            status="COMPLETED"
        )
        jobs_served_period = jobs_served.filter(completed_at__gte=since)

        # --- Earnings ---
        earnings_logs = CreditLog.objects.filter(
            user=user,
            amount__gt=0,
            description__startswith="Earned:"
        )
        total_earnings = earnings_logs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        period_earnings = earnings_logs.filter(
            created_at__gte=since
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        # --- Spending (as consumer) ---
        spending_logs = CreditLog.objects.filter(
            user=user,
            amount__lt=0
        )
        total_spent = abs(spending_logs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"))

        # --- Earnings over time (for charts) ---
        earnings_by_day = list(
            earnings_logs.filter(created_at__gte=since)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(earned=Sum("amount"), jobs=Count("id"))
            .order_by("date")
        )
        for entry in earnings_by_day:
            entry["date"] = entry["date"].isoformat()
            entry["earned"] = float(entry["earned"])

        # --- Per-model breakdown ---
        model_stats = {}
        for job in jobs_served_period:
            model = job.input_data.get("model", "unknown")
            if model not in model_stats:
                model_stats[model] = {"model": model, "jobs": 0, "earned": 0.0}
            model_stats[model]["jobs"] += 1
            model_stats[model]["earned"] += 0.80  # PROVIDER_SHARE

        # --- Recent transactions ---
        recent_logs = CreditLog.objects.filter(user=user).order_by("-created_at")[:50]
        transactions = [{
            "id": log.id,
            "amount": float(log.amount),
            "description": log.description,
            "created_at": log.created_at.isoformat(),
            "type": "earning" if log.amount > 0 else "spending"
        } for log in recent_logs]

        # --- Jobs I submitted (as consumer) ---
        my_jobs = Job.objects.filter(user=user).order_by('-created_at')
        consumer_jobs = [{
            "id": j.id,
            "status": j.status,
            "prompt": j.input_data.get("prompt", "")[:80],
            "model": j.input_data.get("model", ""),
            "cost": str(j.cost) if j.cost else None,
            "result": j.result,
            "created_at": j.created_at.isoformat(),
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        } for j in my_jobs[:50]]

        return Response({
            "provider": {
                "total_earnings": float(total_earnings),
                "period_earnings": float(period_earnings),
                "total_jobs_served": jobs_served.count(),
                "period_jobs_served": jobs_served_period.count(),
                "active_nodes": active_nodes.count(),
                "total_nodes": my_nodes.count(),
                "earnings_by_day": earnings_by_day,
                "model_breakdown": list(model_stats.values()),
            },
            "consumer": {
                "total_spent": float(total_spent),
                "total_jobs": my_jobs.count(),
                "jobs": consumer_jobs,
            },
            "wallet_balance": float(user.wallet_balance),
            "transactions": transactions,
            "period_days": days,
        })
