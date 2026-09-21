#kwanyi :)
# Creating the feedback views.
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FeedbackSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():

            if request.user.is_authenticated:
                Feedback.objects.create(
                    user=request.user,
                    subject=serializer.validated_data["subject"],
                    message=serializer.validated_data["message"]
                )
            else:
                Feedback.objects.create(
                    name=serializer.validated_data["name"],
                    email=serializer.validated_data["email"],
                    subject=serializer.validated_data["subject"],
                    message=serializer.validated_data["message"]
                )

            return Response(
                {"message": "Feedback submitted successfully."},
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )