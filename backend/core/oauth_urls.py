from django.urls import path
from .oauth_views import OAuthCallbackView

urlpatterns = [
    path('', OAuthCallbackView.as_view(), name='oauth-callback'),
]
