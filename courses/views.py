from django.shortcuts import render
from .models import Course, Module, Lesson
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import AuthService, CourseService
from .serializers import RegisterSerializer, LoginSerializer, CourseSerializer
from .permissions import CoursePermission
from rest_framework.permissions import IsAuthenticated,AllowAny

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            auth_service = AuthService()
            tokens = auth_service.register_user(serializer.validated_data)
            return Response({"message": "User registered successfully.", "tokens": tokens}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            auth_service = AuthService()
            tokens = auth_service.login_user(serializer.validated_data)
            return Response({"message": "Login successful.", "tokens": tokens}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseView(APIView):
    serializer_class = CourseSerializer
    service_class = CourseService
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAuthenticated(), CoursePermission()]
        return [AllowAny()]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            course_service = self.service_class()
            try:
                course = course_service.create_course(request.user, **serializer.validated_data)
                return Response({"message": "Course created successfully.", "course_id": course.id}, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    