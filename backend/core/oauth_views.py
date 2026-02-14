"""
OAuth Callback View

After django-allauth completes the OAuth handshake, the user is logged into
Django's session. This view checks if the user is authenticated, generates
JWT tokens (access + refresh), and redirects back to the React frontend
with the tokens as URL hash parameters.

Flow:
  1. User clicks "Sign in with Google" on React frontend
  2. React redirects to /accounts/google/login/
  3. allauth handles OAuth dance → user logs in to Django session
  4. allauth redirects to LOGIN_REDIRECT_URL → /oauth/callback (React)
  5. React calls /api/auth/oauth/callback/ to exchange session for JWT
  6. Backend returns JWT tokens, React stores them
"""
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


from rest_framework.authentication import SessionAuthentication

class OAuthCallbackView(APIView):
    """
    Exchange a valid Django session (set by allauth after OAuth) for JWT tokens.
    Called by the frontend after the OAuth redirect lands on /oauth/callback.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = []

    def get(self, request):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"OAuth Callback Debug: User: {request.user}, Auth: {request.user.is_authenticated}, Session: {request.session.session_key}")
        logger.error(f"Cookies: {request.COOKIES}")
        
        user = request.user
        if not user or not user.is_authenticated:
            return JsonResponse(
                {"error": "Not authenticated. Please complete OAuth login first."},
                status=401
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return JsonResponse({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        })
