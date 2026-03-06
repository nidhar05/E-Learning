from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from .serializers import SignupSerializer

User = get_user_model()

class SignupView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "message": "User created successfully"
            })

        return Response(serializer.errors, status=400)



class LoginView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(
            username=username,
            password=password
        )

        if user is None:

            return Response({
                "error": "Invalid credentials"
            }, status=401)

        refresh = RefreshToken.for_user(user)

        return Response({

            "message": "Login successful",

            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),

            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }

        })