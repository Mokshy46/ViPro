from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class RegistrationSerializer(ModelSerializer):
    
    password = serializers.CharField(write_only = True)
    
    class Meta:
        model = User
        fields = ['email','username','password','password']
        
    
    def create(self, validated_data):
        
        password = validated_data.pop("password")
        
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )
        return user
