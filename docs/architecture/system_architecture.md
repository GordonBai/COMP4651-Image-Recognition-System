# Image Recognition System: Architecture Overview

This document describes the architecture of the Image Recognition System, focusing on the key components and their interactions.

## System Components

The system consists of the following key components:

### 1. Storage Layer

- **MinIO**: Object storage for images and processing results
  - `input-images` bucket: Stores uploaded images
  - `processed-images` bucket: Stores preprocessed images
  - `classification-results` bucket: Stores classification results

- **Redis**: In-memory cache for fast access to recent results
  - Caches classification results with TTL
  - Reduces redundant processing of the same images

### 2. Communication Layer

- **Kafka**: Event streaming platform for asynchronous communication
  - `image-uploads` topic: Events for new image uploads
  - `image-results` topic: Events for completed classifications

- **Nginx**: API Gateway for external communication
  - Route requests to appropriate services
  - Handle authentication and rate limiting

### 3. Processing Layer

- **OpenFaaS Functions**:
  - `image-upload`: Handles image upload and storage in MinIO
  - `image-classifier`: Performs image classification using TensorFlow

- **Kafka Consumers**:
  - `image-process-consumer`: Monitors for new uploads and triggers processing

### 4. Machine Learning Layer

- **TensorFlow Models**:
  - Pre-trained MobileNetV2 model for general image classification
  - Support for custom models

## Data Flow

The system operates with the following data flow:

1. **Image Upload Process**:
   - Client uploads an image via the API Gateway
   - The image is stored in MinIO's `input-images` bucket
   - An event is published to the `image-uploads` Kafka topic

2. **Processing Flow**:
   - Kafka consumer detects new upload event
   - Image is retrieved from MinIO
   - Image is preprocessed and classified using TensorFlow
   - Results are stored in Redis cache and MinIO

3. **Retrieval Flow**:
   - Client requests classification results via API Gateway
   - System first checks Redis cache
   - If not in cache, results are retrieved from MinIO
   - Results are returned to client

## System Architecture Diagram

```
┌───────────┐      ┌───────────┐      ┌───────────┐
│  Client   │─────▶│   Nginx   │─────▶│  OpenFaaS │
│  (User)   │◀─────│ (Gateway) │◀─────│ Functions │
└───────────┘      └───────────┘      └─────┬─────┘
                                            │
                                            ▼
┌───────────┐      ┌───────────┐      ┌───────────┐
│   Redis   │◀────▶│   Kafka   │◀────▶│   MinIO   │
│  (Cache)  │      │(Messaging)│      │ (Storage) │
└───────────┘      └─────┬─────┘      └───────────┘
                          │
                          ▼
                   ┌───────────┐
                   │ TensorFlow│
                   │  (Model)  │
                   └───────────┘
```

## Scalability and High Availability

The system is designed with scalability and high availability in mind:

1. **Horizontal Scaling**:
   - All components can be scaled horizontally
   - OpenFaaS functions automatically scale based on demand
   - Kafka and MinIO can be deployed as clusters

2. **Load Distribution**:
   - Kafka partitioning for parallel processing
   - Redis cache to reduce load on processing system

3. **Fault Tolerance**:
   - Services are containerized for isolation
   - Kafka ensures message delivery even if consumers fail
   - MinIO can be configured for data redundancy

## Security Considerations

The system implements several security measures:

1. **Data Security**:
   - All data can be encrypted at rest in MinIO
   - Network traffic can be encrypted via TLS

2. **Access Control**:
   - MinIO access controls through IAM policies
   - API Gateway can implement authentication and authorization

3. **Isolation**:
   - Services run in isolated containers
   - Network segmentation between components

## Monitoring and Management

The system provides monitoring and management capabilities:

1. **Service Monitoring**:
   - Kafka UI for monitoring message streams
   - MinIO Console for storage management

2. **Logging**:
   - Centralized logging for all components
   - Structured logging format for easy querying

3. **Metrics**:
   - Prometheus metrics exposed by OpenFaaS
   - Performance metrics for processing time and throughput 