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

# Check for Docker Compose plugin instead of standalone docker-compose
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose plugin is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Step 1: Start core services
echo "[Step 1/5] Starting core services (MinIO, Redis, Kafka)..."
docker compose up -d minio redis zookeeper kafka kafka-ui
echo "Waiting for services to initialize..."
sleep 10

# Step 2: Create MinIO buckets
echo "[Step 2/5] Setting up MinIO buckets..."

# Get the container names
MINIO_CONTAINER=$(docker ps --filter "name=minio" --format "{{.Names}}")
KAFKA_CONTAINER=$(docker ps --filter "name=kafka" --format "{{.Names}}")

# Get the Docker network name
NETWORK_NAME=$(docker inspect $MINIO_CONTAINER -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')

# Get Kafka container IP address
KAFKA_IP=$(docker inspect $KAFKA_CONTAINER -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

MC_ALIAS="local"
MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-"minioadmin"}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-"minioadmin"}
INPUT_BUCKET="input-images"
PROCESSED_BUCKET="processed-images"
RESULTS_BUCKET="classification-results"

# Create buckets directly using the MinIO container
docker exec $MINIO_CONTAINER mkdir -p /data/$INPUT_BUCKET
docker exec $MINIO_CONTAINER mkdir -p /data/$PROCESSED_BUCKET
docker exec $MINIO_CONTAINER mkdir -p /data/$RESULTS_BUCKET

# Set up MinIO client in the same container to configure policies and events
docker exec $MINIO_CONTAINER mc alias set $MC_ALIAS http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

# Set download policy for results bucket
docker exec $MINIO_CONTAINER mc anonymous set download $MC_ALIAS/$RESULTS_BUCKET

# Configure Kafka notification target first
docker exec $MINIO_CONTAINER mc admin config set $MC_ALIAS notify_kafka:1 brokers=$KAFKA_IP:9092 topic=minio-events
docker exec $MINIO_CONTAINER mc admin service restart $MC_ALIAS

# Wait for MinIO to restart
sleep 5

# Add event notification for image uploads
docker exec $MINIO_CONTAINER mc event add $MC_ALIAS/$INPUT_BUCKET arn:minio:sqs::1:kafka --event put --suffix .jpg,.jpeg,.png

echo "MinIO setup completed successfully!"

# Step 3: Start OpenFaaS
echo "[Step 3/5] Starting OpenFaaS..."
docker compose up -d openfaas-gateway faas-swarm
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
docker compose up -d nginx

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
echo "docker compose down"
echo "=============================================" 