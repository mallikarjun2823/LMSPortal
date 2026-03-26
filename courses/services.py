from .models import User, Course, Module, Lesson, RoleLookup
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

        # Frontend contract: role is numeric role_num only.
        role_input = data.get('role')
        if isinstance(role_input, RoleLookup):
            raise ValueError("Role must be as an integer.")

        try:
            role_num = int(role_input)
        except (TypeError, ValueError):
            raise ValueError("Role must be as an integer.")

        role_obj = RoleLookup.objects.filter(role_num=role_num).first()
        if not role_obj:
            raise ValueError("Role not found.")

        try:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                role=role_obj
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
    
    def authenticate_user(self, token):
        try:
            refresh = RefreshToken(token)
            user_id = refresh['user_id']
            user = User.objects.get(id=user_id)
            return user
        except Exception:
            return None
            
class CourseService:
    def create_course(self, user, title, description):
        if not title.strip():
            raise ValueError("Title cannot be blank.")
        if not description.strip():
            raise ValueError("Description cannot be blank.")
        # RoleLookup: instructor = role_num 1
        user_role_num = getattr(getattr(user, 'role', None), 'role_num', None)
        if not getattr(user, 'is_authenticated', False) or user_role_num != 1:
            raise ValueError("Only authenticated instructors can create courses.")
        course = Course.objects.create(
            title=title,
            description=description,
            instructor=user
        )
        return course