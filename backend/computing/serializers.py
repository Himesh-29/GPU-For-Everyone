from rest_framework import serializers
from .models import Node, Job

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'
        read_only_fields = ('owner', 'last_heartbeat', 'is_active')

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('user', 'status', 'result', 'completed_at', 'cost', 'node')
