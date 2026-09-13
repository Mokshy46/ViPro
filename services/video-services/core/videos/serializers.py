from rest_framework import serializers
from .models import Video

class VideoModelSerializer(serializers.ModelSerializer):
    
    processed_video = serializers.FileField(read_only = True)
    thumbnail = serializers.ImageField(read_only = True)
    status = serializers.CharField(read_only = True)
    
    class Meta:
        fields = "__all__"
        model = Video