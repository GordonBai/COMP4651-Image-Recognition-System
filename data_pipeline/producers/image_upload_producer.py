import os
import json
import logging
import time
from datetime import datetime
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageUploadProducer:
    """
    Kafka producer for publishing image upload events.
    
    This class handles sending messages to a Kafka topic when images are uploaded
    to the MinIO storage.
    """
    def __init__(self, bootstrap_servers=None, topic=None):
        # Get configuration from environment variables if not provided
        self.bootstrap_servers = bootstrap_servers or os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = topic or os.environ.get('KAFKA_TOPIC_IMAGE_UPLOADS', 'image-uploads')
        
        # Initialize the Kafka producer
        self.producer = self._create_producer()
        logger.info(f"ImageUploadProducer initialized with bootstrap_servers={self.bootstrap_servers}, topic={self.topic}")
    
    def _create_producer(self):
        """
        Create and configure a Kafka producer.
        
        Returns:
            KafkaProducer: Configured Kafka producer
        """
        try:
            return KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {str(e)}")
            raise
    
    def send_upload_event(self, bucket_name, object_name, metadata=None):
        """
        Send an upload event to the Kafka topic.
        
        Args:
            bucket_name (str): The MinIO bucket name
            object_name (str): The object (file) name in the bucket
            metadata (dict, optional): Additional metadata about the image
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if not self.producer:
            logger.error("No Kafka producer available")
            return False
        
        # Create the message payload
        message = {
            'event_type': 'image_uploaded',
            'bucket_name': bucket_name,
            'object_name': object_name,
            'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        # Add metadata if provided
        if metadata:
            message['metadata'] = metadata
        
        try:
            # Use the object name as the key for partitioning
            future = self.producer.send(self.topic, key=object_name, value=message)
            # Wait for the send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Image upload event sent: topic={record_metadata.topic}, "
                      f"partition={record_metadata.partition}, offset={record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send upload event for {object_name}: {str(e)}")
            return False
    
    def close(self):
        """
        Close the Kafka producer.
        """
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Example usage
if __name__ == "__main__":
    producer = ImageUploadProducer()
    
    # Example: Send an image upload event
    producer.send_upload_event(
        bucket_name="input-images",
        object_name="example.jpg",
        metadata={"content_type": "image/jpeg", "size": 1024}
    )
    
    # Close the producer
    producer.close() 