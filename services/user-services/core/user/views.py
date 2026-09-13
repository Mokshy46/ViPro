from django.shortcuts import render
from .serializers import RegistrationSerializer
from rest_framework.generics import CreateAPIView
from django.contrib.auth import get_user_model


User = get_user_model()




class RegisterCreateAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer