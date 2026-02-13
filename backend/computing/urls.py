from django.urls import path
from .views import JobSubmissionView, JobDetailView

urlpatterns = [
    path('submit-job/', JobSubmissionView.as_view(), name='submit-job'),
    path('jobs/<int:job_id>/', JobDetailView.as_view(), name='job-detail'),
]
