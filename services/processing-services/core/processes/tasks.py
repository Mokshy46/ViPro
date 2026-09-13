import subprocess
import boto3,os

from pathlib import Path
from celery import shared_task
from .rabbitmq import publish_video_status
import botocore.exceptions

from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

@shared_task(bind = True)
def process_video(self,video_id, video_path):

    
        
        object_key = video_path

        try:
            local_input_path = Path("/tmp") / Path(object_key).name
            s3.download_file("videos", object_key, str(local_input_path))
            
        except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as error:

            if self.request.retries < 3 :
                self.retry(exc = error, countdown = 10, max_retries = 3)
                
            else:
                publish_video_status(video_id=video_id, video_status="failed", processed_video=None, thumbnail=None)   
                raise

            
        publish_video_status(video_id=video_id, video_status="processing", processed_video=None, thumbnail=None)
        
        
        filename = Path(object_key).stem
        local_output_path = Path("/tmp") / f"{filename}_720p.mp4"
        local_thumbnail_path = Path("/tmp") / f"{filename}_tb.jpg"
        

        video_output_key = f"processed/{filename}_720p.mp4"
        thumbnail_output_key = f"thumbnail/{filename}_tb.jpg"
        
        
        

        ffmpeg_command = [
                "/usr/bin/ffmpeg",

                "-i",
                str(local_input_path),

                "-vf",
                "scale=-2:720",

                "-c:v",
                "libx264",

                "-c:a",
                "aac",

                "-movflags",
                "+faststart",

                "-y",

                str(local_output_path),
            ]

        result = subprocess.run(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        if result.returncode != 0:
            publish_video_status(video_id=video_id, video_status="failed", processed_video=None, thumbnail=None)   
            raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")



        thumbnail_command = [
                "/usr/bin/ffmpeg",
                
                "-i",
                str(local_input_path),
                
                "-ss",
                "00:00:05",

                "-frames:v",
                "1",

                "-y",

                str(local_thumbnail_path), 
            ]
        result = subprocess.run(
                thumbnail_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        if result.returncode != 0:
            publish_video_status(video_id=video_id, video_status="failed", processed_video=None, thumbnail=None)   
            raise RuntimeError(f"Thumbnail generation failed:\n{result.stderr}")


        try:
            s3.upload_file(str(local_output_path), "videos", video_output_key)
            s3.upload_file(str(local_thumbnail_path), "videos", thumbnail_output_key)
            
        except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as error:
            
            if self.request.retries < 3 :
                self.retry(exc = error, countdown = 10, max_retries = 3)
                
            else:
                publish_video_status(video_id=video_id, video_status="failed", processed_video=None, thumbnail=None)   
                raise

    


        local_input_path.unlink(missing_ok=True)
        local_output_path.unlink(missing_ok=True)
        local_thumbnail_path.unlink(missing_ok=True)

        publish_video_status(video_id=video_id, video_status="completed", processed_video=video_output_key, thumbnail=thumbnail_output_key)

        return {
            "video_id": str(video_id),
            "video": video_output_key,
            "thumbnail": thumbnail_output_key,
        }
        
        
  