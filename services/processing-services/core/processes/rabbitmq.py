import pika, json



def publish_video_status(video_id, video_status):
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    
    channel = connection.channel()
    
    channel.queue_declare(queue='status', durable=True, arguments={'x-queue-type': 'quorum'})
    
    message = {
        "video_id" : str(video_id),
        "status": str(video_status),
       
    }

    channel.basic_publish(exchange='', routing_key='status', body=json.dumps(message))

    connection.close()    