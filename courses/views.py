from django.shortcuts import render
from .models import Course, Module, Lesson
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import AuthService
from .serializers import RegisterSerializer, LoginSerializer

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

# Create your views here.
