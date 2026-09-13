import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


import pika, sys, os, json
from .models import Video


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='status', durable=True, arguments={'x-queue-type': 'quorum'})

    def callback(ch, method, properties, body):
        
        message = json.loads(body)
        video_id = message["video_id"]
        video_status = message["status"]
        processed_video = message["processed_video"]
        thumbnail = message["thumbnail"]
        
        print(f"status updated to {video_status}")
    
        video = Video.objects.get(id = video_id)
        video.status = video_status
        video.processed_video = processed_video
        video.thumbnail = thumbnail
        video.save()
        
        ch.basic_ack(delivery_tag = method.delivery_tag)


    channel.basic_consume(
        queue="status",
        on_message_callback=callback
    )
    channel.basic_qos(prefetch_count=1)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)