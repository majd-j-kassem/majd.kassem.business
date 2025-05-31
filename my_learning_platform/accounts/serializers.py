# auth_system/accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    # We don't want the password to be readable after creation
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True) # Ensure email is required and validated
    # --- MUTATION: Add required=False ---
    #email = serializers.EmailField(required=False) 
      # --- End Mutation ---
    class Meta:
        model = User
        # Fields to include in the serializer. username is required by default for Django's User model
        fields = ('username', 'email', 'password', 'password2')
        # Optionally add extra restrictions or requirements
        # extra_kwargs = {'username': {'required': True}} # Username is required by default

    def validate_email(self, value):
        """
        Check that the email is not already in use.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use.")
        return value

    def validate(self, attrs):
        # Call parent validation first (e.g., checks for unique username if applicable)
        super().validate(attrs)

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # You could add more cross-field validations here if needed

        return attrs

    def create(self, validated_data):
        # Remove password2 as it's not part of the User model
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    # Allows login with either username or email
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    # No create or update methods needed for a login serializer as it doesn't create/update a model instance
    # Validation will happen in the view where we call authenticate()
    
class DeleteUserByEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)