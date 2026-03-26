from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import User, Course


class AuthAndCourseTests(APITestCase):
    def setUp(self):
        # create an instructor user
        self.instructor = User.objects.create_user(
            username='instructor1',
            email='instructor@example.com',
            password='password',
            role='INSTRUCTOR'
        )

    def test_register_endpoint(self):
        url = reverse('register')
        payload = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'pass1234',
            'role': 'STUDENT'
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', resp.data)

    def test_login_and_create_course_as_instructor(self):
        # Login to get tokens
        login_url = reverse('login')
        resp = self.client.post(login_url, {'username': 'instructor1', 'password': 'password'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        tokens = resp.data.get('tokens')
        self.assertIsNotNone(tokens)
        access = tokens.get('access')
        self.assertIsNotNone(access)

        # Create a course using access token
        create_url = reverse('course-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        course_payload = {'title': 'Django', 'description': 'Basic Django course'}
        resp2 = self.client.post(create_url, course_payload, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        # verify course exists
        course_id = resp2.data.get('course_id')
        self.assertIsNotNone(course_id)
        self.assertTrue(Course.objects.filter(id=course_id, title='Django').exists())
from django.test import TestCase

# Create your tests here.
