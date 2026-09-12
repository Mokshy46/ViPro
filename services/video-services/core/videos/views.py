from .serializers import VideoModelSerializer
from .models import Video
from rest_framework.generics import ListCreateAPIView, DestroyAPIView
from .rabbitmq import publish_video_job



class VideoListCreateAPIView(ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoModelSerializer

    def perform_create(self, serializer):

        video = serializer.save()

        publish_video_job(video_id= video.id, video_path=video.video_file)    


class VideoDestroyAPIView(DestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoModelSerializer
    
    lookup_field = 'id'


