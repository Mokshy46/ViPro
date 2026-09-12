from django.urls import path
from .views import VideoListCreateAPIView, VideoDestroyAPIView

urlpatterns = [
    path('video/', VideoListCreateAPIView.as_view(), name='video'),
    path('video/delete/<uuid:id>/', VideoDestroyAPIView.as_view(), name='video-delete' ),
]
