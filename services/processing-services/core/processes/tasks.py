import subprocess
import boto3

from pathlib import Path
from celery import shared_task
from .rabbitmq import publish_video_status

from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
)

@shared_task
def process_video(video_id, video_path):

    try:
        
        object_key = video_path

        local_input_path = Path("/tmp") / Path(object_key).name
        s3.download_file("videos", object_key, str(local_input_path))
        
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
            raise RuntimeError(f"Thumbnail generation failed:\n{result.stderr}")


        s3.upload_file(str(local_output_path), "videos", video_output_key)
        s3.upload_file(str(local_thumbnail_path), "videos", thumbnail_output_key)


    
        local_input_path.unlink(missing_ok=True)
        local_output_path.unlink(missing_ok=True)
        local_thumbnail_path.unlink(missing_ok=True)

        publish_video_status(video_id=video_id, video_status="completed", processed_video=video_output_key, thumbnail=thumbnail_output_key)

        return {
            "video_id": str(video_id),
            "video": video_output_key,
            "thumbnail": thumbnail_output_key,
        }
        
    except:
        publish_video_status(video_id=video_id, video_status="failed", processed_video=None, thumbnail=None)   
        raise     