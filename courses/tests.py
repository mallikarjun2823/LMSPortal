from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import User, Course, RoleLookup


class AuthAndCourseTests(APITestCase):
    def setUp(self):
        # ensure role lookup rows exist and create an instructor user
        instructor_role, _ = RoleLookup.objects.get_or_create(role_num='INST', defaults={'role_name': 'INSTRUCTOR'})
        RoleLookup.objects.get_or_create(role_num='STUD', defaults={'role_name': 'STUDENT'})
        RoleLookup.objects.get_or_create(role_num='ADMIN', defaults={'role_name': 'ADMINISTRATOR'})

        self.instructor = User.objects.create_user(
            username='instructor1',
            email='instructor@example.com',
            password='password',
            role=instructor_role
        )

    def test_register_endpoint(self):
        url = reverse('register')
        payload = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'pass1234',
            'role': 'STUD'
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

        # Create a course as authenticated instructor.
        # force_authenticate keeps test focused on role/permission behavior.
        create_url = reverse('course-list-create')
        self.client.force_authenticate(user=self.instructor)
        course_payload = {'title': 'Django', 'description': 'Basic Django course'}
        resp2 = self.client.post(create_url, course_payload, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        # verify course exists
        course_id = resp2.data.get('id')
        self.assertIsNotNone(course_id)
        self.assertTrue(Course.objects.filter(id=course_id, title='Django').exists())
