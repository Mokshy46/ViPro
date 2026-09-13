import pika, sys, os, json
from .tasks import process_video
from dotenv import load_dotenv

load_dotenv()

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST")))
    channel = connection.channel()

    channel.queue_declare(queue='video_processing', durable=True, arguments={'x-queue-type': 'quorum'})

    def callback(ch, method, properties, body):
        
        message = json.loads(body)
        video_id = message["video_id"]
        video_path = message["video_path"]
        
        print(f"recived video {video_id}")
        
        process_video.delay(video_id,video_path)
        
        ch.basic_ack(delivery_tag = method.delivery_tag)


    channel.basic_consume(
        queue="video_processing",
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