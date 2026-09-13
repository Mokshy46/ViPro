import pika
import json,os
from dotenv import load_dotenv

load_dotenv()

def publish_video_job(video_id, video_path):
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST")))

    channel = connection.channel()

    channel.queue_declare(queue='video_processing', durable=True, arguments={'x-queue-type': 'quorum'})    
    
    message = {
        "video_id": str(video_id),
        "video_path":str(video_path),
    }
    
    channel.basic_publish(exchange='', routing_key='video_processing', body=json.dumps(message))
    
    connection.close()
    