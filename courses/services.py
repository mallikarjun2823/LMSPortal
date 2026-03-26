from .models import User, Course, Module, Lesson
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class AuthService:
    def generate_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    def register_user(self, data):
        if User.objects.filter(username=data['username']).exists():
            raise ValueError("Username already exists.")
        if User.objects.filter(email=data['email']).exists():
            raise ValueError("Email already exists.")
        if data['role'] not in [choice[0] for choice in User.ROLE_CHOICES]:
            raise ValueError(f"Role must be one of: {', '.join([choice[0] for choice in User.ROLE_CHOICES])}.")
        try:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                role=data['role']
            )
            user.save()
            return self.generate_tokens_for_user(user)

        except Exception as e:
            raise ValueError(f"Error registering user: {str(e)}")
    
    def login_user(self, data):
        try:
            user = User.objects.get(username=data['username'])
            if user.check_password(data['password']):
                return self.generate_tokens_for_user(user)
            else:
                raise ValueError("Invalid password.")
        except User.DoesNotExist:
            raise ValueError("User does not exist.")