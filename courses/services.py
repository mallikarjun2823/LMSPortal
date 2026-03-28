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

        # Serializer returns role as string role_num key (e.g., 'INST', 'STUD')
        role_num = data.get('role')
        if not role_num:
            raise ValueError("Role is required.")

        role_obj = RoleLookup.objects.filter(role_num=role_num).first()
        if not role_obj:
            raise ValueError(f"Role '{role_num}' not found.")

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

    def list_courses(self, user):
        """List courses based on user role.
        
        - Students: return courses they are enrolled in
        - Instructors: return courses they teach
        - Others: return empty queryset
        """
        if not getattr(user, 'is_authenticated', False):
            return Course.objects.none()
        
        user_role_num = getattr(getattr(user, 'role', None), 'role_num', None)
        
        if user_role_num == 'STUD':
            # Return courses the student is enrolled in
            return user.enrolled_courses.all().select_related('instructor').prefetch_related('enrolled_students')
        elif user_role_num == 'INST':
            # Return courses the instructor teaches
            return user.instructed_courses.all().select_related('instructor').prefetch_related('enrolled_students')
        else:
            # For other roles (ADMIN, etc.), return empty
            return Course.objects.none()
    
    def create_course(self, user, title, description):
        if not title.strip():
            raise ValueError("Title cannot be blank.")
        if not description.strip():
            raise ValueError("Description cannot be blank.")
        # RoleLookup: instructor uses role_num 'INST'
        user_role_num = getattr(getattr(user, 'role', None), 'role_num', None)
        if not getattr(user, 'is_authenticated', False) or user_role_num != 'INST':
            raise ValueError("Only authenticated instructors can create courses.")
        course = Course.objects.filter(title=title).first()
        if course:
            raise ValueError("A course with this title already exists.")
        course = Course.objects.filter(description=description).first()
        if course:
            raise ValueError("A course with this description already exists.")
        course = Course.objects.create(
            title=title,
            description=description,
            instructor=user
        )
        return Course.objects.select_related('instructor').get(id=course.id)