"""Root URL configuration for the GPU Connect project."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/core/', include('core.urls')),
    path('api/computing/', include('computing.urls')),
    path('api/payments/', include('payments.urls')),
    # OAuth (django-allauth) — handles /accounts/google/login/ etc.
    path('accounts/', include('allauth.urls')),
    # Custom OAuth callback to issue JWT tokens
    path('api/auth/oauth/callback/', include('core.oauth_urls')),
]
