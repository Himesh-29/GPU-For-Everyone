from django.db import models
from django.conf import settings

class Node(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    node_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    gpu_info = models.JSONField(default=dict)
    is_active = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.node_id})"

class Job(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='jobs', on_delete=models.CASCADE)
    node = models.ForeignKey(Node, related_name='jobs', on_delete=models.SET_NULL, null=True, blank=True)
    task_type = models.CharField(max_length=50) # e.g., 'inference', 'training'
    input_data = models.JSONField() # Docker image, args, etc
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"Job {self.id} - {self.status}"
