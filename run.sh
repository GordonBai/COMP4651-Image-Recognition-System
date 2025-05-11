#!/bin/bash

# Image Recognition System Startup Script

set -e

# Display header
echo "============================================="
echo "  Image Recognition System Startup Script"
echo "============================================="

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Step 1: Start core services
echo "[Step 1/5] Starting core services (MinIO, Redis, Kafka)..."
docker-compose up -d minio redis zookeeper kafka kafka-ui
echo "Waiting for services to initialize..."
sleep 10

# Step 2: Create MinIO buckets
echo "[Step 2/5] Setting up MinIO buckets..."
docker run --rm --network=host \
    -v $(pwd)/cloud_storage/minio/scripts:/scripts \
    -e MINIO_ENDPOINT=http://localhost:9000 \
    -e MINIO_ROOT_USER=minioadmin \
    -e MINIO_ROOT_PASSWORD=minioadmin \
    minio/mc /bin/sh /scripts/setup_buckets.sh

# Step 3: Start OpenFaaS
echo "[Step 3/5] Starting OpenFaaS..."
docker-compose up -d openfaas-gateway faas-swarm
echo "Waiting for OpenFaaS to initialize..."
sleep 10

# Step 4: Deploy OpenFaaS functions
echo "[Step 4/5] Deploying OpenFaaS functions..."
cd serverless_functions
if command -v faas-cli &> /dev/null; then
    faas-cli up -f stack.yml
else
    echo "Warning: OpenFaaS CLI (faas-cli) is not installed."
    echo "Please install it to deploy functions:"
    echo "curl -sSL https://cli.openfaas.com | sudo sh"
    echo "Then run: cd serverless_functions && faas-cli up -f stack.yml"
fi
cd ..

# Step 5: Start API Gateway
echo "[Step 5/5] Starting API Gateway..."
docker-compose up -d nginx

# Start the Kafka consumer
echo "[Optional] Starting Kafka consumer for image processing..."
echo "To start the consumer, run:"
echo "python -m data_pipeline.consumers.image_process_consumer"

# Display access information
echo ""
echo "============================================="
echo "  System is ready!"
echo "============================================="
echo ""
echo "Access points:"
echo "- API Gateway: http://localhost:8080"
echo "- MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)"
echo "- Kafka UI: http://localhost:8085"
echo ""
echo "API Endpoints:"
echo "- Upload image: POST http://localhost:8080/api/upload"
echo "- Classify image: POST http://localhost:8080/api/classify"
echo ""
echo "To stop the system, run:"
echo "docker-compose down"
echo "=============================================" 