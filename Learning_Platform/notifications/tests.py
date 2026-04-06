from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from comments.models import Comment
from courses.models import Course
from enrollments.models import Enrollment
from notifications.models import Notification
from users.models import CustomUser
from videos.models import Video


class NotificationApiTests(APITestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username="instructor",
            password="password123",
            role="instructor",
        )
        self.student = CustomUser.objects.create_user(
            username="student",
            password="password123",
            role="student",
        )
        self.other_student = CustomUser.objects.create_user(
            username="other-student",
            password="password123",
            role="student",
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Notification API Course",
            description="Used for serializer tests.",
        )

    def test_list_returns_only_unread_notifications_for_receiver(self):
        unread = Notification.objects.create(
            receiver=self.instructor,
            sender=self.student,
            message="Unread notification",
        )
        Notification.objects.create(
            receiver=self.instructor,
            sender=self.other_student,
            message="Read notification",
            is_read=True,
        )
        Notification.objects.create(
            receiver=self.student,
            sender=self.instructor,
            message="Someone else's notification",
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(reverse("notifications"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], unread.id)

    def test_list_supports_all_and_read_filters_with_target_metadata(self):
        lesson_video = Video.objects.create(
            course=self.course,
            title="Routing Target",
            video_file=SimpleUploadedFile(
                "target.mp4",
                b"fake video bytes",
                content_type="video/mp4",
            ),
            duration=8,
            order=1,
        )
        unread = Notification.objects.create(
            receiver=self.instructor,
            sender=self.student,
            notification_type=Notification.TYPE_ENROLLMENT,
            message="Enrollment target",
            course=self.course,
        )
        read_notification = Notification.objects.create(
            receiver=self.instructor,
            sender=self.other_student,
            notification_type=Notification.TYPE_NEW_LESSON,
            message="Lesson target",
            course=self.course,
            video=lesson_video,
            is_read=True,
        )

        self.client.force_authenticate(user=self.instructor)

        all_response = self.client.get(f"{reverse('notifications')}?status=all")
        read_response = self.client.get(f"{reverse('notifications')}?status=read")

        self.assertEqual(all_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(all_response.data), 2)
        self.assertEqual(len(read_response.data), 1)

        all_items = {item["id"]: item for item in all_response.data}
        self.assertEqual(all_items[unread.id]["notification_type"], Notification.TYPE_ENROLLMENT)
        self.assertEqual(all_items[unread.id]["target_url"], f"/course/{self.course.id}")
        self.assertEqual(
            all_items[read_notification.id]["target_url"],
            f"/course/{self.course.id}/watch/{lesson_video.id}",
        )
        self.assertEqual(read_response.data[0]["id"], read_notification.id)

    def test_comment_notifications_serialize_deep_link_targets(self):
        top_level_comment = Comment.objects.create(
            user=self.student,
            course=self.course,
            text="Top-level discussion",
        )
        reply_comment = Comment.objects.create(
            user=self.other_student,
            course=self.course,
            parent=top_level_comment,
            text="Follow-up reply",
        )

        top_level_notification = Notification.objects.create(
            receiver=self.instructor,
            sender=self.student,
            notification_type=Notification.TYPE_COMMENT,
            message="Top level",
            course=self.course,
            comment=top_level_comment,
        )
        reply_notification = Notification.objects.create(
            receiver=self.instructor,
            sender=self.other_student,
            notification_type=Notification.TYPE_COMMENT_REPLY,
            message="Reply",
            course=self.course,
            comment=reply_comment,
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(f"{reverse('notifications')}?status=all")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = {item["id"]: item for item in response.data}
        self.assertEqual(
            items[top_level_notification.id]["target_url"],
            f"/course/{self.course.id}?comment={top_level_comment.id}#comment-{top_level_comment.id}",
        )
        self.assertEqual(
            items[reply_notification.id]["target_url"],
            (
                f"/course/{self.course.id}"
                f"?comment={top_level_comment.id}&reply={reply_comment.id}"
                f"#reply-{reply_comment.id}"
            ),
        )

    def test_mark_notification_read_only_updates_receivers_notification(self):
        notification = Notification.objects.create(
            receiver=self.instructor,
            sender=self.student,
            message="Please read me",
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.put(
            reverse("mark-notification-read", args=[notification.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_notifications_read_only_updates_current_user(self):
        own_notifications = [
            Notification.objects.create(
                receiver=self.instructor,
                sender=self.student,
                message="One",
            ),
            Notification.objects.create(
                receiver=self.instructor,
                sender=self.other_student,
                message="Two",
            ),
        ]
        other_notification = Notification.objects.create(
            receiver=self.student,
            sender=self.instructor,
            message="Other user",
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.put(reverse("mark-all-notifications-read"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        for notification in own_notifications:
            notification.refresh_from_db()
            self.assertTrue(notification.is_read)

        other_notification.refresh_from_db()
        self.assertFalse(other_notification.is_read)


class NotificationCreationFromCommentsTests(APITestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username="course-owner",
            password="password123",
            role="instructor",
        )
        self.student = CustomUser.objects.create_user(
            username="student-one",
            password="password123",
            role="student",
        )
        self.other_student = CustomUser.objects.create_user(
            username="student-two",
            password="password123",
            role="student",
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Testing Notifications",
            description="A course for notification tests.",
        )
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.other_student, course=self.course)

    def test_top_level_comment_notifies_instructor(self):
        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            reverse("comment-list-create"),
            {
                "course": self.course.id,
                "text": "This lesson helped a lot.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(
            receiver=self.instructor,
            sender=self.student,
        )
        self.assertTrue(
            notification.message == f"{self.student.username} commented on your course: {self.course.title}"
        )
        self.assertEqual(notification.notification_type, Notification.TYPE_COMMENT)
        self.assertEqual(notification.course_id, self.course.id)
        self.assertIsNotNone(notification.comment_id)

    def test_reply_notifies_original_comment_author(self):
        parent_comment = Comment.objects.create(
            user=self.student,
            course=self.course,
            text="Can someone explain the last step?",
        )

        self.client.force_authenticate(user=self.other_student)
        response = self.client.post(
            reverse("comment-list-create"),
            {
                "course": self.course.id,
                "parent": parent_comment.id,
                "text": "Yes, here is how it works.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(
            receiver=self.student,
            sender=self.other_student,
        )
        self.assertTrue(
            notification.message == f"{self.other_student.username} replied to your comment"
        )
        self.assertEqual(notification.notification_type, Notification.TYPE_COMMENT_REPLY)
        self.assertEqual(notification.course_id, self.course.id)
        self.assertIsNotNone(notification.comment_id)

    def test_reply_to_own_comment_does_not_create_self_notification(self):
        parent_comment = Comment.objects.create(
            user=self.student,
            course=self.course,
            text="I found the answer myself.",
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            reverse("comment-list-create"),
            {
                "course": self.course.id,
                "parent": parent_comment.id,
                "text": "Adding more detail for future readers.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(
            Notification.objects.filter(
                receiver=self.student,
                sender=self.student,
                message=f"{self.student.username} replied to your comment",
            ).exists()
        )


class NotificationCreationFromEnrollmentsAndVideosTests(APITestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username="video-owner",
            password="password123",
            role="instructor",
        )
        self.other_instructor = CustomUser.objects.create_user(
            username="other-instructor",
            password="password123",
            role="instructor",
        )
        self.student = CustomUser.objects.create_user(
            username="enrolled-student",
            password="password123",
            role="student",
        )
        self.second_student = CustomUser.objects.create_user(
            username="second-student",
            password="password123",
            role="student",
        )
        self.unenrolled_student = CustomUser.objects.create_user(
            username="unenrolled-student",
            password="password123",
            role="student",
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Backend Notifications",
            description="Testing additional notification sources.",
        )

    def test_new_enrollment_notifies_course_instructor_once(self):
        self.client.force_authenticate(user=self.student)

        first_response = self.client.post(reverse("enroll", args=[self.course.id]))
        second_response = self.client.post(reverse("enroll", args=[self.course.id]))

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        notification = Notification.objects.get(
            receiver=self.instructor,
            sender=self.student,
        )
        self.assertEqual(
            Notification.objects.filter(
                receiver=self.instructor,
                sender=self.student,
                message=f"{self.student.username} enrolled in your course: {self.course.title}",
            ).count(),
            1,
        )
        self.assertEqual(notification.notification_type, Notification.TYPE_ENROLLMENT)
        self.assertEqual(notification.course_id, self.course.id)

    def test_new_video_notifies_only_enrolled_students(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.second_student, course=self.course)

        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(
            reverse("video-list-create"),
            {
                "course": self.course.id,
                "title": "Async Tasks",
                "duration": 12,
                "order": 1,
                "video_file": SimpleUploadedFile(
                    "lesson.mp4",
                    b"fake video bytes",
                    content_type="video/mp4",
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        student_notification = Notification.objects.get(
            receiver=self.student,
            sender=self.instructor,
        )
        self.assertTrue(
            Notification.objects.filter(
                receiver=self.student,
                sender=self.instructor,
                message=f"New lesson added to {self.course.title}: Async Tasks",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                receiver=self.second_student,
                sender=self.instructor,
                message=f"New lesson added to {self.course.title}: Async Tasks",
            ).exists()
        )
        self.assertEqual(student_notification.notification_type, Notification.TYPE_NEW_LESSON)
        self.assertEqual(student_notification.course_id, self.course.id)
        self.assertIsNotNone(student_notification.video_id)
        self.assertFalse(
            Notification.objects.filter(
                receiver=self.unenrolled_student,
                message=f"New lesson added to {self.course.title}: Async Tasks",
            ).exists()
        )

    def test_other_instructor_cannot_upload_video_to_someone_elses_course(self):
        self.client.force_authenticate(user=self.other_instructor)
        response = self.client.post(
            reverse("video-list-create"),
            {
                "course": self.course.id,
                "title": "Unauthorized Upload",
                "duration": 10,
                "order": 1,
                "video_file": SimpleUploadedFile(
                    "forbidden.mp4",
                    b"fake video bytes",
                    content_type="video/mp4",
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Notification.objects.filter(
                message=f"New lesson added to {self.course.title}: Unauthorized Upload",
            ).exists()
        )
