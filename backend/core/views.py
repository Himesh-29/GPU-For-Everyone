"""Views for the core module — registration, profiles, and agent tokens."""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, views, status
from rest_framework.response import Response

from .models import AgentToken
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """Register a new user account."""
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user


class AgentTokenGenerateView(views.APIView):
    """Generate a new agent token. Returns the raw token ONCE."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Generate a new agent token; returns the raw token once."""
        label = request.data.get('label', 'Default Agent')

        # Limit to 5 active tokens per user
        active_count = AgentToken.objects.filter(user=request.user, is_active=True).count()
        if active_count >= 5:
            return Response(
                {"error": "Maximum 5 active tokens allowed. Revoke an existing token first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        agent_token, raw_token = AgentToken.generate(user=request.user, label=label)
        return Response({
            "token": raw_token,
            "id": agent_token.id,
            "label": agent_token.label,
            "created_at": agent_token.created_at.isoformat(),
            "message": "Save this token — it will NOT be shown again."
        }, status=status.HTTP_201_CREATED)


class AgentTokenListView(views.APIView):
    """List all active agent tokens for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List all active agent tokens for the current user."""
        tokens = AgentToken.objects.filter(user=request.user, is_active=True)
        data = [{
            "id": t.id,
            "label": t.label,
            "created_at": t.created_at.isoformat(),
            "last_used": t.last_used.isoformat() if t.last_used else None,
            "token_prefix": f"gpc_{t.token_hash[:8]}...",
        } for t in tokens]
        return Response(data)


class AgentTokenRevokeView(views.APIView):
    """Revoke an agent token by ID."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, token_id):
        """Revoke an agent token by ID."""
        try:
            token = AgentToken.objects.get(id=token_id, user=request.user, is_active=True)
            token.is_active = False
            token.save()
            return Response({"status": "revoked", "id": token_id})
        except AgentToken.DoesNotExist:
            return Response(
                {"error": "Token not found or already revoked."},
                status=status.HTTP_404_NOT_FOUND
            )


class HealthCheckView(views.APIView):
    """Health check endpoint for cron jobs and monitoring. No auth required."""
    permission_classes = [permissions.AllowAny]

    def get(self, _request):
        """Return service health status."""
        return Response({
            "status": "healthy",
            "service": "GPU Connect API",
            "timestamp": timezone.now().isoformat(),
            "version": "2.1"
        })
