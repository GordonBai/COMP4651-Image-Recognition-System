#!/bin/bash

# This script initializes the MinIO buckets needed for the image recognition system

set -e

# MinIO client configuration
MC_ALIAS="local"
MINIO_ENDPOINT=${MINIO_ENDPOINT:-"http://localhost:9000"}
MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-"minioadmin"}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-"minioadmin"}

# Bucket names
INPUT_BUCKET="input-images"
PROCESSED_BUCKET="processed-images"
RESULTS_BUCKET="classification-results"

echo "Setting up MinIO client..."
mc alias set $MC_ALIAS $MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

echo "Creating buckets if they don't exist..."
mc mb --ignore-existing $MC_ALIAS/$INPUT_BUCKET
mc mb --ignore-existing $MC_ALIAS/$PROCESSED_BUCKET
mc mb --ignore-existing $MC_ALIAS/$RESULTS_BUCKET

echo "Setting bucket policies..."
# Allow public read access to the results bucket
mc policy set download $MC_ALIAS/$RESULTS_BUCKET

# Add a notification configuration to trigger processing when images are uploaded
mc event add $MC_ALIAS/$INPUT_BUCKET arn:minio:sqs::1:kafka --event put --suffix .jpg,.jpeg,.png

echo "MinIO setup completed successfully!" 