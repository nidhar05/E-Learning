from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course
from users.models import CustomUser


class InstructorCourseListViewTests(APITestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username='instructor-one',
            password='password123',
            role='instructor',
        )
        self.other_instructor = CustomUser.objects.create_user(
            username='instructor-two',
            password='password123',
            role='instructor',
        )

        self.own_course = Course.objects.create(
            instructor=self.instructor,
            title='My Course',
            description='Only mine should appear.',
        )
        Course.objects.create(
            instructor=self.other_instructor,
            title='Someone Else Course',
            description='This should stay hidden.',
        )

    def test_requires_authentication(self):
        response = self.client.get(reverse('my-courses'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_authenticated_instructor_courses(self):
        self.client.force_authenticate(user=self.instructor)

        response = self.client.get(reverse('my-courses'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.own_course.id)
