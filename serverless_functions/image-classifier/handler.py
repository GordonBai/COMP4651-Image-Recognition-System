import os
import sys
import json
import tempfile
import logging
from urllib.parse import unquote
from minio import Minio
import redis

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to path to import the image_processing module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the image classifier
try:
    from image_processing.services.image_classifier import ImageClassifier
    classifier = ImageClassifier()
except ImportError:
    logger.error("Error importing ImageClassifier. Make sure the image_processing module is available.")
    classifier = None


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


def get_redis_client():
    """
    Create and configure a Redis client based on environment variables.
    
    Returns:
        Redis: Configured Redis client, or None if configuration fails
    """
    try:
        host = os.environ.get('REDIS_HOST', 'redis')
        port = int(os.environ.get('REDIS_PORT', 6379))
        password = os.environ.get('REDIS_PASSWORD', '')
        
        client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True
        )
        
        # Test connection
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Error connecting to Redis: {str(e)}")
        return None


def handle(req):
    """
    OpenFaaS function handler for image classification.
    
    This function can handle several input formats:
    1. Image data directly in the request body
    2. URL-encoded MinIO object reference: bucket_name/object_name
    3. JSON with MinIO reference: {"bucket": "...", "object": "..."}
    
    Args:
        req: The request body
        
    Returns:
        str: JSON string containing classification results
    """
    if not classifier:
        return json.dumps({"error": "Image classifier not available"})
    
    try:
        # Check if the input is JSON
        try:
            input_json = json.loads(req)
            bucket_name = input_json.get('bucket')
            object_name = input_json.get('object')
            
            if bucket_name and object_name:
                # Process MinIO reference from JSON
                return process_minio_object(bucket_name, object_name)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Check if input is a MinIO reference string (bucket/object)
        if isinstance(req, str) and '/' in req:
            parts = unquote(req).split('/', 1)
            if len(parts) == 2:
                bucket_name, object_name = parts
                return process_minio_object(bucket_name, object_name)
        
        # Process direct image data
        return process_image_data(req)
        
    except Exception as e:
        logger.error(f"Error in function handler: {str(e)}")
        return json.dumps({"error": str(e)})


def process_minio_object(bucket_name, object_name):
    """
    Process an image stored in MinIO.
    
    Args:
        bucket_name (str): MinIO bucket name
        object_name (str): Object name in the bucket
        
    Returns:
        str: JSON string containing classification results
    """
    # First check if results are already in Redis
    redis_client = get_redis_client()
    if redis_client:
        result_key = f"classification:{bucket_name}:{object_name}"
        cached_result = redis_client.get(result_key)
        if cached_result:
            logger.info(f"Returning cached results for {bucket_name}/{object_name}")
            return cached_result
    
    # If not in cache, process the image
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Get MinIO client and download the image
            minio_client = get_minio_client()
            minio_client.fget_object(bucket_name, object_name, temp_file.name)
            
            # Classify the image
            results = classifier.classify_image(temp_file.name)
            
            # Create the response
            response = {
                "bucket": bucket_name,
                "object": object_name,
                "results": results
            }
            
            # Cache the results in Redis
            if redis_client:
                result_json = json.dumps(response)
                redis_client.set(result_key, result_json)
                redis_client.expire(result_key, 3600)  # Expire after 1 hour
            
            return json.dumps(response)
            
        except Exception as e:
            logger.error(f"Error processing MinIO object: {str(e)}")
            return json.dumps({"error": f"Error processing {bucket_name}/{object_name}: {str(e)}"})
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except:
                pass


def process_image_data(image_data):
    """
    Process image data directly from the request.
    
    Args:
        image_data: Binary image data
        
    Returns:
        str: JSON string containing classification results
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Save the image data to a temporary file
            if isinstance(image_data, str):
                image_data = image_data.encode('utf-8')
            
            temp_file.write(image_data)
            temp_file.flush()
            
            # Classify the image
            results = classifier.classify_image(temp_file.name)
            
            # Create the response
            response = {
                "source": "direct_upload",
                "results": results
            }
            
            return json.dumps(response)
            
        except Exception as e:
            logger.error(f"Error processing image data: {str(e)}")
            return json.dumps({"error": f"Error processing image data: {str(e)}"})
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except:
                pass 