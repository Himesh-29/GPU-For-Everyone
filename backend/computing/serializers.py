"""Serializers for the computing module."""
from rest_framework import serializers
from .models import Node, Job


class NodeSerializer(serializers.ModelSerializer):
    """Serializer for GPU Node instances."""

    class Meta:
        """NodeSerializer metadata."""
        model = Node
        fields = '__all__'
        read_only_fields = ('owner', 'last_heartbeat', 'is_active')

class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job instances."""

    class Meta:
        """JobSerializer metadata."""
        model = Job
        fields = '__all__'
        read_only_fields = ('user', 'status', 'result', 'completed_at', 'cost', 'node')
