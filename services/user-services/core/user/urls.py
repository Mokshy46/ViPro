from django.urls import path
from .views import RegisterCreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



urlpatterns = [
    path('register/', RegisterCreateAPIView.as_view(), name="register" ),
    path('login/', TokenObtainPairView.as_view(), name= "login"),
    path('token/refresh/', TokenRefreshView.as_view(), name= "refresh"),

]