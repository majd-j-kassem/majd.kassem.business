Unit Tests: 
These are the smallest tests you can write. They focus on testing individual, isolated components (units) of your code in isolation. The goal is to verify that each unit of code works correctly on its own. In your Django app, units could be:

A single model's method.
A specific view function or class method.
A serializer's validation or data representation.
A utility function.
Unit tests should be fast to run and shouldn't rely on external dependencies like databases (though Django's TestCase provides a test database setup by default, you often use mocking for true isolation).

Integration Tests: 
These tests verify that different units or components of your application work correctly together. They test the interactions and data flow between different parts of your system. For your Django REST API authentication system, integration tests would involve:

Testing if a user can register successfully through the API (testing the interaction between the serializer, view, and model).
Testing if a user can log in and receive a token (testing the interaction between the login view, serializer, and authentication backend).
Testing if an authenticated user can access a protected endpoint.
Integration tests are typically slower than unit tests because they involve more of your application's stack and often interact with the database.

/api/register/: Mapped to RegisterAPIView
/api/login/: Mapped to LoginAPIView
/api/logout/: Mapped to LogoutAPIView
/api/user/: Mapped to UserDetailAPIView 