from django.db import models
import uuid


class Video(models.Model):
    
    
    def video_upload_path(instance, video_path):
        extension = video_path.rsplit(".", 1)[-1]
        return f"input/{instance.id}.{extension}"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user_id = models.UUIDField(default=uuid.uuid4, editable=False)
    
    video_file = models.FileField(upload_to= video_upload_path)
    title = models.TextField()
    
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.UPLOADED)     
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    processed_video = models.FileField(null=True, blank=True)
    thumbnail = models.ImageField(null=True, blank=False)
    
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    