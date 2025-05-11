# Image Recognition System: Setup Guide

This guide provides detailed instructions for setting up and running the Image Recognition System.

## Prerequisites

Before starting, make sure you have the following installed on your system:

1. **Docker and Docker Compose**
   - Docker: [Installation Guide](https://docs.docker.com/get-docker/)
   - Docker Compose: [Installation Guide](https://docs.docker.com/compose/install/)

2. **Python 3.8+**
   - [Python Downloads](https://www.python.org/downloads/)
   - Required for running local components and tests

3. **OpenFaaS CLI** (optional, but recommended)
   - Install with: `curl -sSL https://cli.openfaas.com | sudo sh`
   - Required for deploying OpenFaaS functions

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/image-recognition-system.git
cd image-recognition-system
```

### 2. Install Python Dependencies

Create a virtual environment and install the required Python packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the System

Use the provided script to start all the services:

```bash
./run.sh
```

This script will:
1. Start MinIO, Redis, Zookeeper, Kafka, and Kafka UI
2. Create required MinIO buckets
3. Start OpenFaaS services
4. Deploy OpenFaaS functions
5. Start the API Gateway (Nginx)

### 4. Start the Image Processing Consumer (Optional)

If you want to process images automatically when they're uploaded, start the Kafka consumer:

```bash
# In a new terminal
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m data_pipeline.consumers.image_process_consumer
```

### 5. Verify the Setup

You can access the following services in your browser:

- **API Gateway**: http://localhost:8080
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadmin)
- **Kafka UI**: http://localhost:8085

Run the API tests to verify the system is working correctly:

```bash
# Assuming you have an image file to test with
python tests/test_api_endpoints.py path/to/your/image.jpg
```

## Component Configuration

### Environment Variables

The system uses environment variables for configuration. You can modify these in the `.env` file:

```
# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=minio:9000
MINIO_SECURE=false

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_IMAGE_UPLOADS=image-uploads
KAFKA_TOPIC_IMAGE_RESULTS=image-results

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Model Configuration
MODEL_NAME=mobilenet_v2
MODEL_INPUT_SIZE=224
MODEL_CONFIDENCE_THRESHOLD=0.5
```

### API Endpoints

The system provides the following API endpoints:

1. **Upload Image**
   - URL: `POST http://localhost:8080/api/upload`
   - Body (JSON):
     ```json
     {
       "image_data": "base64_encoded_image_data",
       "content_type": "image/jpeg",
       "bucket": "input-images"
     }
     ```

2. **Classify Image**
   - URL: `POST http://localhost:8080/api/classify`
   - Body (JSON):
     ```json
     {
       "bucket": "input-images",
       "object": "image_name.jpg"
     }
     ```

## Troubleshooting

### 1. Services not starting

If any service fails to start, check the logs with:

```bash
docker-compose logs [service_name]
```

### 2. OpenFaaS functions not deploying

Make sure the OpenFaaS CLI is installed and the gateway is running:

```bash
faas-cli list --gateway http://localhost:8081
```

If there are issues, try deploying the functions manually:

```bash
cd serverless_functions
faas-cli up -f stack.yml --gateway http://localhost:8081
```

### 3. No classification results

Make sure the model files are accessible. The system uses pre-trained models from TensorFlow. 
If you need custom models, place them in `image_processing/models/pretrained/`.

## Stopping the System

To stop all services:

```bash
docker-compose down
```

To also remove persistent volumes:

```bash
docker-compose down -v
``` 