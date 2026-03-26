from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from courses.models import Course, Module, Lesson


class Command(BaseCommand):
    help = "Seed the database with example Users, Courses, Modules and Lessons."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seeded objects before creating new ones.",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        if options["clear"]:
            self.stdout.write("Clearing existing seeded data...")
            # remove lessons, modules, courses and example users (safe narrow delete)
            Lesson.objects.all().delete()
            Module.objects.all().delete()
            Course.objects.all().delete()
            User.objects.filter(username__in=["instructor1", "student1", "admin"]).delete()

        with transaction.atomic():
            # Create users
            instructor, created = User.objects.get_or_create(
                username="instructor1",
                defaults={"email": "instructor@example.com", "role": "INSTRUCTOR"},
            )
            if created:
                instructor.set_password("password")
                instructor.save()

            student, created = User.objects.get_or_create(
                username="student1",
                defaults={"email": "student@example.com", "role": "STUDENT"},
            )
            if created:
                student.set_password("password")
                student.save()

            admin, created = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@example.com",
                    "role": "ADMINISTRATOR",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            if created:
                admin.set_password("password")
                admin.save()

            # Create a sample course
            course, created = Course.objects.get_or_create(
                title="Intro to Testing",
                defaults={
                    "description": "A short sample course created by seed command.",
                    "instructor": instructor,
                },
            )

            # Ensure instructor relation is set if course already existed
            if not created and course.instructor_id != instructor.id:
                course.instructor = instructor
                course.save()

            # Create modules and lessons
            for m in range(1, 4):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    module_number=m,
                    defaults={"title": f"Module {m}"},
                )

                for l in range(1, 4):
                    Lesson.objects.get_or_create(
                        module=module,
                        lesson_number=l,
                        defaults={
                            "title": f"Lesson {l}",
                            "content": f"Sample content for lesson {l} of module {m}.",
                        },
                    )

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
