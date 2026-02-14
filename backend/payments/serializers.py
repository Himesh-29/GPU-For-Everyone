"""Serializers for transaction and credit log models."""
from rest_framework import serializers

from .models import Transaction, CreditLog


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for deposit/withdrawal transactions."""

    class Meta:
        """Meta options for TransactionSerializer."""

        model = Transaction
        fields = '__all__'
        read_only_fields = ('status', 'user')

class CreditLogSerializer(serializers.ModelSerializer):
    """Serializer for wallet credit log entries."""

    class Meta:
        """Meta options for CreditLogSerializer."""

        model = CreditLog
        fields = '__all__'
