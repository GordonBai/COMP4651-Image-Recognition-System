import os
import logging
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MinioClient:
    """
    A utility class for interacting with MinIO object storage.
    
    This class provides a simplified interface for common MinIO operations
    such as uploading, downloading, and listing objects.
    """
    def __init__(self, endpoint=None, access_key=None, secret_key=None, secure=None):
        # Get configuration from environment variables if not provided
        self.endpoint = endpoint or os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or os.environ.get('MINIO_ROOT_USER', 'minioadmin')  
        self.secret_key = secret_key or os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin')
        
        # Parse secure flag (default to False)
        if secure is None:
            self.secure = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
        else:
            self.secure = secure
        
        # Initialize the MinIO client
        self.client = self._create_client()
        logger.info(f"MinioClient initialized with endpoint={self.endpoint}, secure={self.secure}")
    
    def _create_client(self):
        """
        Create and configure a MinIO client.
        
        Returns:
            Minio: Configured MinIO client
        """
        try:
            return Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
        except Exception as e:
            logger.error(f"Failed to create MinIO client: {str(e)}")
            raise
    
    def bucket_exists(self, bucket_name):
        """
        Check if a bucket exists.
        
        Args:
            bucket_name (str): Name of the bucket
            
        Returns:
            bool: True if the bucket exists, False otherwise
        """
        try:
            return self.client.bucket_exists(bucket_name)
        except S3Error as e:
            logger.error(f"Error checking if bucket exists: {str(e)}")
            return False
    
    def create_bucket(self, bucket_name):
        """
        Create a bucket if it doesn't exist.
        
        Args:
            bucket_name (str): Name of the bucket to create
            
        Returns:
            bool: True if the bucket was created or already exists, False otherwise
        """
        try:
            if not self.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket created: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error creating bucket: {str(e)}")
            return False
    
    def upload_file(self, bucket_name, object_name, file_path, content_type=None):
        """
        Upload a file to MinIO.
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name to assign to the object in MinIO
            file_path (str): Path to the file to upload
            content_type (str, optional): Content type of the file
            
        Returns:
            bool: True if the upload was successful, False otherwise
        """
        try:
            # Ensure the bucket exists
            if not self.bucket_exists(bucket_name):
                self.create_bucket(bucket_name)
            
            # Upload the file
            self.client.fput_object(
                bucket_name, object_name, file_path, content_type=content_type
            )
            logger.info(f"File uploaded: {file_path} -> {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False
    
    def upload_bytes(self, bucket_name, object_name, data, content_type=None):
        """
        Upload bytes data to MinIO.
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name to assign to the object in MinIO
            data (bytes): Bytes data to upload
            content_type (str, optional): Content type of the data
            
        Returns:
            bool: True if the upload was successful, False otherwise
        """
        try:
            # Ensure the bucket exists
            if not self.bucket_exists(bucket_name):
                self.create_bucket(bucket_name)
            
            # Upload the bytes data
            from io import BytesIO
            data_stream = BytesIO(data)
            data_size = len(data)
            
            self.client.put_object(
                bucket_name, object_name, data_stream, data_size, content_type=content_type
            )
            logger.info(f"Bytes uploaded: {len(data)} bytes -> {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading bytes: {str(e)}")
            return False
    
    def download_file(self, bucket_name, object_name, file_path):
        """
        Download a file from MinIO.
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name of the object in MinIO
            file_path (str): Path where the file should be saved
            
        Returns:
            bool: True if the download was successful, False otherwise
        """
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            logger.info(f"File downloaded: {bucket_name}/{object_name} -> {file_path}")
            return True
        except S3Error as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False
    
    def download_bytes(self, bucket_name, object_name):
        """
        Download an object as bytes from MinIO.
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name of the object in MinIO
            
        Returns:
            bytes: The object data as bytes, or None if an error occurred
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            logger.info(f"Object downloaded as bytes: {bucket_name}/{object_name}")
            return data
        except S3Error as e:
            logger.error(f"Error downloading object as bytes: {str(e)}")
            return None
    
    def list_objects(self, bucket_name, prefix=None, recursive=True):
        """
        List objects in a bucket.
        
        Args:
            bucket_name (str): Name of the bucket
            prefix (str, optional): Prefix to filter objects
            recursive (bool): Whether to list objects recursively
            
        Returns:
            list: List of object names
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects: {str(e)}")
            return []
    
    def delete_object(self, bucket_name, object_name):
        """
        Delete an object from MinIO.
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name of the object in MinIO
            
        Returns:
            bool: True if the deletion was successful, False otherwise
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Object deleted: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting object: {str(e)}")
            return False
    
    def get_object_url(self, bucket_name, object_name, expires=3600):
        """
        Get a presigned URL for an object.
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name of the object in MinIO
            expires (int): URL expiration time in seconds
            
        Returns:
            str: Presigned URL for the object
        """
        try:
            url = self.client.presigned_get_object(bucket_name, object_name, expires)
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Create a MinIO client
    minio_client = MinioClient()
    
    # Create a test bucket
    bucket_name = "test-bucket"
    minio_client.create_bucket(bucket_name)
    
    # Upload a test file
    minio_client.upload_file(bucket_name, "test.txt", "test.txt", content_type="text/plain")
    
    # List objects in the bucket
    objects = minio_client.list_objects(bucket_name)
    print(f"Objects in bucket {bucket_name}: {objects}")
    
    # Delete the test object
    minio_client.delete_object(bucket_name, "test.txt") 