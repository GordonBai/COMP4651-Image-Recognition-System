import os
import sys
import json
import logging
import tempfile
from kafka import KafkaConsumer
from minio import Minio
import redis

# Add the project root to path to import the image_processing module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from image_processing.services.image_classifier import ImageClassifier

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageProcessConsumer:
    """
    Kafka consumer for processing uploaded images.
    
    This class listens for image upload events, retrieves the images from MinIO,
    processes them using the image classifier, and saves the results.
    """
    def __init__(self, bootstrap_servers=None, topic=None, 
                minio_endpoint=None, minio_access_key=None, minio_secret_key=None,
                redis_host=None, redis_port=None, redis_password=None):
        # Kafka configuration
        self.bootstrap_servers = bootstrap_servers or os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = topic or os.environ.get('KAFKA_TOPIC_IMAGE_UPLOADS', 'image-uploads')
        
        # MinIO configuration
        self.minio_endpoint = minio_endpoint or os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
        self.minio_access_key = minio_access_key or os.environ.get('MINIO_ROOT_USER', 'minioadmin')
        self.minio_secret_key = minio_secret_key or os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin')
        self.minio_secure = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
        
        # Redis configuration
        self.redis_host = redis_host or os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = redis_port or int(os.environ.get('REDIS_PORT', 6379))
        self.redis_password = redis_password or os.environ.get('REDIS_PASSWORD', '')
        
        # Initialize components
        self.consumer = self._create_consumer()
        self.minio_client = self._create_minio_client()
        self.redis_client = self._create_redis_client()
        self.classifier = ImageClassifier()
        
        logger.info(f"ImageProcessConsumer initialized with bootstrap_servers={self.bootstrap_servers}, "
                   f"topic={self.topic}, minio_endpoint={self.minio_endpoint}")
    
    def _create_consumer(self):
        """
        Create and configure a Kafka consumer.
        
        Returns:
            KafkaConsumer: Configured Kafka consumer
        """
        try:
            return KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                group_id='image-processing-group'
            )
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise
    
    def _create_minio_client(self):
        """
        Create and configure a MinIO client.
        
        Returns:
            Minio: Configured MinIO client
        """
        try:
            return Minio(
                self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=self.minio_secure
            )
        except Exception as e:
            logger.error(f"Failed to create MinIO client: {str(e)}")
            raise
    
    def _create_redis_client(self):
        """
        Create and configure a Redis client.
        
        Returns:
            Redis: Configured Redis client
        """
        try:
            r = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                decode_responses=True
            )
            # Test connection
            r.ping()
            return r
        except Exception as e:
            logger.error(f"Failed to create Redis client: {str(e)}")
            # Redis is optional, so return None if it fails
            return None
    
    def process_image(self, bucket_name, object_name):
        """
        Process an image from MinIO.
        
        Args:
            bucket_name (str): The MinIO bucket name
            object_name (str): The object (file) name in the bucket
            
        Returns:
            dict: Classification results
        """
        # Create a temporary file to store the downloaded image
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            try:
                # Download the image from MinIO
                logger.info(f"Downloading image {object_name} from bucket {bucket_name}")
                self.minio_client.fget_object(bucket_name, object_name, temp_file.name)
                
                # Classify the image
                logger.info(f"Classifying image {object_name}")
                results = self.classifier.classify_image(temp_file.name)
                
                # Save the results to the processed bucket
                results_dict = {
                    'object_name': object_name,
                    'bucket_name': bucket_name,
                    'classifications': results
                }
                
                # Save results to Redis if available
                if self.redis_client:
                    result_key = f"classification:{bucket_name}:{object_name}"
                    self.redis_client.set(result_key, json.dumps(results_dict))
                    self.redis_client.expire(result_key, 86400)  # Expire after 24 hours
                
                return results_dict
                
            except Exception as e:
                logger.error(f"Error processing image {object_name}: {str(e)}")
                raise
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def start_consuming(self):
        """
        Start consuming messages from the Kafka topic.
        """
        logger.info(f"Starting to consume messages from topic: {self.topic}")
        
        try:
            for message in self.consumer:
                try:
                    # Extract the message value
                    event = message.value
                    logger.info(f"Received event: {event}")
                    
                    # Process the event if it's an image upload
                    if event.get('event_type') == 'image_uploaded':
                        bucket_name = event.get('bucket_name')
                        object_name = event.get('object_name')
                        
                        if bucket_name and object_name:
                            # Process the image
                            results = self.process_image(bucket_name, object_name)
                            logger.info(f"Image processed successfully: {object_name}")
                            logger.debug(f"Classification results: {results}")
                        else:
                            logger.warning(f"Invalid event structure: {event}")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.close()
    
    def close(self):
        """
        Close all connections.
        """
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis client closed")


# Example usage
if __name__ == "__main__":
    consumer = ImageProcessConsumer()
    consumer.start_consuming() 