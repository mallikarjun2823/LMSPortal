from .models import User,Course, Module, Lesson
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if not value.strip():
            raise serializers.ValidationError("Username cannot be blank.")

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        return value
    def validate_email(self, value):
        if not value.strip():
            raise serializers.ValidationError("Email cannot be blank.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        
        return value
    
    def validate_role(self, value):
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}.")
        return value
        
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        if not data['username'].strip():
            raise serializers.ValidationError("Username cannot be blank.")

        if not data['password'].strip():
            raise serializers.ValidationError("Password cannot be blank.")

        user = User.objects.filter(username=data['username']).first()
        if not user:
            raise serializers.ValidationError("User with this username does not exist.")
        return data
