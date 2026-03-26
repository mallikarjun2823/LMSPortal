from .models import User,Course, Module, Lesson, RoleLookup
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
        # Frontend contract: incoming payload must send numeric role_num.
        raw_role = self.initial_data.get('role') if hasattr(self, 'initial_data') else None
        try:
            int(raw_role)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Role must be an integer role_num.")

        # DRF may already convert FK id to RoleLookup instance by this point.
        if isinstance(value, RoleLookup):
            role_num = value.role_num
        else:
            try:
                role_num = int(value)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Role must be an integer role_num.")

        if not RoleLookup.objects.filter(role_num=role_num).exists():
            valid_roles = [f"{r.role_num}:{r.role_name}" for r in RoleLookup.objects.all()]
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}.")
        return role_num
        
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

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description','created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Description cannot be blank.")
        return value
    
    