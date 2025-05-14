from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token as AuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .serializers import UserRegisterSerializer, UserLoginSerializer

User = get_user_model()

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny] # Allow anyone to register

    # Optional: Customize the response if needed
    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LoginAPIView(APIView):
    permission_classes = [AllowAny] # Allow anyone to attempt to log in
    serializer_class = UserLoginSerializer # Assign the serializer class

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username_or_email = serializer.validated_data['username_or_email']
            password = serializer.validated_data['password']

            # Try to authenticate using username first
            user = authenticate(request, username=username_or_email, password=password)

            if user is None:
                # If username didn't work, try with email
                try:
                    user_by_email = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    # User not found by email either
                    pass

            if user is not None:
                # User is valid, log them in and get/create token
                login(request, user) # This sets the session, useful even with token
                token, created = AuthToken.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_200_OK)
            else:
                # Authentication failed
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        # If serializer is not valid, return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can log out

    def post(self, request, *args, **kwargs):
        try:
            # Delete the user's authentication token
            request.user.auth_token.delete()
            # Log out the user from the session (important if you use sessions too)
            logout(request)
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
             # This catch is broad, you might want to handle specific exceptions
            return Response({'error': f'An error occurred during logout: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can access
    serializer_class = UserRegisterSerializer # Use the register serializer to display user data (adjust fields in serializer if needed)
    queryset = User.objects.all() # Required for RetrieveAPIView, though we override get_object

    def get_object(self):
        # Return the currently authenticated user
        return self.request.user

    # Optional: Customize the response data if needed
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     # You can modify serializer.data here before returning
    #     return Response(serializer.data)