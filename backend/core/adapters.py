"""Custom social-account adapter for allauth OAuth integration."""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import redirect


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """Auto-signup and error-redirect adapter for social logins."""

    def is_auto_signup_allowed(  # pylint: disable=unused-argument
        self, request, sociallogin
    ):
        """Always allow automatic sign-up for social accounts."""
        return True

    def populate_user(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, request, sociallogin, data
    ):
        """Fill in username from social data if not already set."""
        user = super().populate_user(request, sociallogin, data)
        if hasattr(user, 'username') and not user.username:
            user.username = (
                data.get('login')
                or data.get('email', '').split('@')[0]
                or "user"
            )
        return user

    def on_authentication_error(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, request, provider, error=None, exception=None, extra_context=None
    ):
        """
        If OAuth fails, don't show the 'dirty' 8000 error page.
        Redirect back to the frontend login page with an error flag.
        """
        frontend_login_url = f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        return redirect(frontend_login_url)
