import os
import sys
import json
import base64
import argparse
import requests
from urllib.parse import urljoin


def test_upload(api_url, image_path):
    """
    Test the image upload API endpoint.
    
    Args:
        api_url (str): Base URL of the API gateway
        image_path (str): Path to the test image
    
    Returns:
        dict: The response from the upload endpoint
    """
    print(f"Testing image upload API with image: {image_path}")
    
    # Read the image file
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Convert to base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Create the request payload
    payload = {
        'image_data': image_base64,
        'content_type': 'image/jpeg',
        'bucket': 'input-images'
    }
    
    # Make the request
    upload_url = urljoin(api_url, '/api/upload')
    response = requests.post(upload_url, json=payload)
    
    print(f"\nUpload response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print("Upload response data:")
        print(json.dumps(response_data, indent=2))
        
        return response_data
    except:
        print(f"Error parsing response: {response.text}")
        return None


def test_classify(api_url, bucket, object_name):
    """
    Test the image classification API endpoint.
    
    Args:
        api_url (str): Base URL of the API gateway
        bucket (str): MinIO bucket name
        object_name (str): Object name in the bucket
    
    Returns:
        dict: The response from the classification endpoint
    """
    print(f"\nTesting image classification API with object: {bucket}/{object_name}")
    
    # Create the request payload
    payload = {
        'bucket': bucket,
        'object': object_name
    }
    
    # Make the request
    classify_url = urljoin(api_url, '/api/classify')
    response = requests.post(classify_url, json=payload)
    
    print(f"\nClassification response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print("Classification response data:")
        print(json.dumps(response_data, indent=2))
        
        return response_data
    except:
        print(f"Error parsing response: {response.text}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test API endpoints")
    parser.add_argument("image_path", help="Path to the image file to use for testing")
    parser.add_argument("--api_url", default="http://localhost:8080", help="URL of the API gateway")
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found: {args.image_path}")
        sys.exit(1)
    
    # Test upload endpoint
    upload_response = test_upload(args.api_url, args.image_path)
    
    if not upload_response or 'error' in upload_response:
        print("\nUpload test failed.")
        sys.exit(1)
    
    # Test classify endpoint with the uploaded image
    bucket = upload_response.get('bucket')
    object_name = upload_response.get('object')
    
    if bucket and object_name:
        classify_response = test_classify(args.api_url, bucket, object_name)
        
        if not classify_response or 'error' in classify_response:
            print("\nClassification test failed.")
            sys.exit(1)
            
        print("\nAPI tests completed successfully.")
        sys.exit(0)
    else:
        print("\nCould not get bucket/object from upload response.")
        sys.exit(1) 