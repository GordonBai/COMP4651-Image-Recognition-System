import os
import sys
import json
import logging
import uuid
from datetime import datetime
from minio import Minio
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_minio_client():
    """
    Create and configure a MinIO client based on environment variables.
    
    Returns:
        Minio: Configured MinIO client
    """
    endpoint = os.environ.get('MINIO_ENDPOINT', 'minio:9000')
    access_key = os.environ.get('MINIO_ROOT_USER', 'minioadmin')
    secret_key = os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin')
    secure = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
    
    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )


def get_kafka_producer():
    """
    Create and configure a Kafka producer based on environment variables.
    
    Returns:
        KafkaProducer: Configured Kafka producer, or None if configuration fails
    """
    try:
        bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        
        return KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {str(e)}")
        return None


def handle(req):
    """
    OpenFaaS function handler for image upload.
    
    This function accepts image data, uploads it to MinIO, and publishes an event to Kafka.
    
    Args:
        req: The request body (should be a JSON string)
        
    Returns:
        str: JSON string containing the upload result
    """
    try:
        # Parse input
        try:
            input_data = json.loads(req)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input"})
        
        # Get image data
        image_data = input_data.get('image_data')
        if not image_data:
            return json.dumps({"error": "Missing image_data in request"})
        
        # Get image metadata
        content_type = input_data.get('content_type', 'image/jpeg')
        bucket_name = input_data.get('bucket', 'input-images')
        object_name = input_data.get('object_name')
        
        # Generate a unique object name if not provided
        if not object_name:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            object_name = f"{timestamp}_{uuid.uuid4().hex}.jpg"
        
        # Upload the image to MinIO
        minio_client = get_minio_client()
        
        # Check if bucket exists, create if not
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
        
        # Convert base64 string to bytes if necessary
        import base64
        if isinstance(image_data, str):
            # Check if it's a base64 string
            if image_data.startswith('data:image'):
                # Extract the base64 part from data URL
                image_data = image_data.split(',')[1]
            
            # Decode base64
            try:
                image_data = base64.b64decode(image_data)
            except Exception as e:
                logger.error(f"Failed to decode base64 image: {str(e)}")
                return json.dumps({"error": "Invalid base64 image data"})
        
        # Upload image to MinIO
        from io import BytesIO
        image_stream = BytesIO(image_data)
        minio_client.put_object(
            bucket_name,
            object_name,
            image_stream,
            length=len(image_data),
            content_type=content_type
        )
        logger.info(f"Image uploaded to {bucket_name}/{object_name}")
        
        # Send Kafka message
        kafka_producer = get_kafka_producer()
        if kafka_producer:
            topic = os.environ.get('KAFKA_TOPIC_IMAGE_UPLOADS', 'image-uploads')
            
            message = {
                'event_type': 'image_uploaded',
                'bucket_name': bucket_name,
                'object_name': object_name,
                'content_type': content_type,
                'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            kafka_producer.send(topic, key=object_name, value=message)
            kafka_producer.flush()
            logger.info(f"Event sent to Kafka topic: {topic}")
        
        # Generate URL for the uploaded image
        try:
            url = minio_client.presigned_get_object(
                bucket_name, object_name, expires=24*60*60
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            url = None
        
        # Return the result
        result = {
            "status": "success",
            "bucket": bucket_name,
            "object": object_name,
            "url": url
        }
        
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in function handler: {str(e)}")
        return json.dumps({"error": str(e)}) 