from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'wallet_balance')
        read_only_fields = ('wallet_balance',)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Minimum 8 characters, must pass Django password validators."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')

    def validate_password(self, value):
        """Run Django's built-in password validators."""
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'USER')
        )
        return user
