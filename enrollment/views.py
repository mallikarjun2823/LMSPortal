from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from courses.models import Course, User
from courses.serializers import CourseSerializer

from .models import Enrollment
from .serializers import EnrollmentSerializer, EnrollmentInviteSerializer
from .permissions import IsInstructor


class EnrollmentListView(APIView):

	permission_classes = [IsAuthenticated]

	def get(self, request):
		user = request.user
		user_role_num = getattr(getattr(user, "role", None), "role_num", None)

		if user_role_num == "INST":
			# For instructors: list courses they teach with enrollment details
			courses = (
				Course.objects.filter(instructor=user)
				.prefetch_related("enrollments__user")
			)
			result = []
			for course in courses:
				invited = []
				active = []
				closed = []
				for enr in course.enrollments.all():
					data = EnrollmentSerializer(enr).data
					if enr.status == Enrollment.Status.INVITED:
						invited.append(data)
					elif enr.status == Enrollment.Status.ACTIVE:
						active.append(data)
					else:
						# COMPLETED / WITHDRAWN / SUSPENDED treated as "closed"
						closed.append(data)
				result.append(
					{
						"course": CourseSerializer(course).data,
						"enrollments": {
							"invited": invited,
							"active": active,
							"closed": closed,
						},
					}
				)
			return Response(result)

		# Default: treat as student view
		qs = Enrollment.objects.filter(user=user).select_related("course")
		invited = []
		active = []
		closed = []
		for enr in qs:
			data = EnrollmentSerializer(enr).data
			if enr.status == Enrollment.Status.INVITED:
				invited.append(data)
			elif enr.status == Enrollment.Status.ACTIVE:
				active.append(data)
			else:
				closed.append(data)

		return Response(
			{
				"invited": invited,
				"active": active,
				"closed": closed,
			}
		)


class EnrollmentDetailView(APIView):

	permission_classes = [IsAuthenticated]

	def _get_object(self, enrollment_id: int) -> Enrollment:
		return get_object_or_404(Enrollment.objects.select_related("course", "user"), id=enrollment_id)

	def _check_access(self, user: User, enrollment: Enrollment) -> bool:
		user_role_num = getattr(getattr(user, "role", None), "role_num", None)
		if user_role_num == "INST" and enrollment.course.instructor_id == user.id:
			return True
		if enrollment.user_id == user.id:
			return True
		return False

	def get(self, request, enrollment_id: int):
		enrollment = self._get_object(enrollment_id)
		if not self._check_access(request.user, enrollment):
			return Response({"error": "You do not have access to this enrollment."}, status=status.HTTP_403_FORBIDDEN)
		return Response(EnrollmentSerializer(enrollment).data)

	def post(self, request, enrollment_id: int):
		"""Perform an action on a single enrollment.

		Currently supports:
		- Students: {"action": "accept"} to accept an INVITED enrollment.
		"""

		enrollment = self._get_object(enrollment_id)
		user = request.user
		if not self._check_access(user, enrollment):
			return Response({"error": "You do not have access to this enrollment."}, status=status.HTTP_403_FORBIDDEN)

		user_role_num = getattr(getattr(user, "role", None), "role_num", None)
		action = request.data.get("action")

		if user_role_num == "STUD":
			if action != "accept":
				return Response({"error": "Unsupported action for student."}, status=status.HTTP_400_BAD_REQUEST)
			if enrollment.user_id != user.id:
				return Response({"error": "You can only act on your own enrollments."}, status=status.HTTP_403_FORBIDDEN)
			if enrollment.status != Enrollment.Status.INVITED:
				return Response({"error": "Only invited enrollments can be accepted."}, status=status.HTTP_400_BAD_REQUEST)
			enrollment.status = Enrollment.Status.ACTIVE
			enrollment.activated_at = timezone.now()
			enrollment.save(update_fields=["status", "activated_at", "updated_at"])
			return Response(EnrollmentSerializer(enrollment).data)

		return Response({"error": "No supported action for this role."}, status=status.HTTP_400_BAD_REQUEST)


class EnrollmentInviteView(APIView):
	"""Invite a single student to enroll in a course.

	Rules:
	- Request user must be an instructor.
	- They must be the instructor for the target course.
	- Target student must not already have an ACTIVE or INVITED enrollment
	  for this course.
	"""

	permission_classes = [IsAuthenticated, IsInstructor]

	def post(self, request, course_id: int):
		serializer = EnrollmentInviteSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		course = get_object_or_404(Course, id=course_id)

		# Ensure the requesting instructor actually owns this course
		if course.instructor_id != request.user.id:
			return Response(
				{"error": "You are not the instructor for this course."},
				status=status.HTTP_403_FORBIDDEN,
			)

		student_id = serializer.validated_data["student_id"]
		student = get_object_or_404(User, id=student_id)

		existing = Enrollment.objects.filter(user=student, course=course).order_by("-id").first()
		if existing and existing.status in (Enrollment.Status.ACTIVE, Enrollment.Status.INVITED):
			if existing.status == Enrollment.Status.ACTIVE:
				msg = "Student is already enrolled in this course."
			else:
				msg = "An invitation has already been sent to this student for this course."
			return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

		enrollment = Enrollment.objects.create(
			user=student,
			course=course,
			status=Enrollment.Status.INVITED,
			invited_at=timezone.now(),
		)

		return Response(
			EnrollmentSerializer(enrollment).data,
			status=status.HTTP_201_CREATED,
		)

