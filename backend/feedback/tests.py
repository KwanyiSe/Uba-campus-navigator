from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Feedback

User = get_user_model()

"""creating tests cases for the feedback app you can run this tests with 
'python manage.py test feedback'.
"""

class FeedbackAPITestCase(APITestCase):

    def setUp(self):
        self.url = "/api/feedback/submit/"

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )

    def get_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)

    def test_guest_can_submit_feedback(self):
        """
        Guest users should be able to submit feedback.
        """

        data = {
            "name": "Bodeh Delton",
            "email": "Bodeh@example.com",
            "subject": "Campus Navigation",
            "message": "Library building missing."
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            Feedback.objects.count(),
            1
        )

        feedback = Feedback.objects.first()

        self.assertEqual(feedback.name, "Bodeh Delton")
        self.assertEqual(feedback.email, "Bodeh@example.com")
        self.assertIsNone(feedback.user)

    def test_guest_requires_name(self):
        """
        Guest feedback must include name.
        """

        data = {
            "email": "Bodeh@example.com",
            "subject": "Campus Navigation",
            "message": "Library building missing."
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_guest_requires_email(self):
        """
        Guest feedback must include email.
        """

        data = {
            "name": "bodeh Delton",
            "subject": "Campus Navigation",
            "message": "Library building missing."
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_authenticated_user_can_submit_feedback(self):
        """
        Logged-in users should not need name/email.
        """

        token = self.get_access_token()

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        data = {
            "subject": "Attendance Issue",
            "message": "I was marked absent."
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        feedback = Feedback.objects.first()

        self.assertEqual(
            feedback.user,
            self.user
        )

        self.assertIsNone(feedback.name)
        self.assertIsNone(feedback.email)

    def test_feedback_default_status(self):
        """
        New feedback should default to pending.
        """

        Feedback.objects.create(
            name="Kwnayi",
            email="kwanyi@example.com",
            subject="Test",
            message="Just Testing the apis  Message"
        )

        feedback = Feedback.objects.first()

        self.assertEqual(
            feedback.status,
            "pending"
        )