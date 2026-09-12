from rest_framework import serializers
from .models import Video

class VideoModelSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = "__all__"
        model = Video