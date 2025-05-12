# Image Recognition System

## Overview
A scalable image recognition system built with open-source technologies:
- MinIO for object storage
- Kafka for event streaming
- OpenFaaS for serverless functions
- TensorFlow for image classification
- Nginx for API gateway

## Features
- Image upload and storage
- Deep learning-based image classification
- Scalable processing pipeline
- RESTful API endpoints

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- OpenFaaS CLI (for function deployment)

### Setup
1. Clone this repository
   ```bash
   git clone https://github.com/your-username/image-recognition-system.git
   cd image-recognition-system
   ```

2. Copy and configure environment variables
   ```bash
   conda activate image-recognition
   pip install -r requirements.txt
   ```

3. Start the services
   ```bash
   docker-compose up -d
   ```

4. Deploy OpenFaaS functions
   ```bash
   cd serverless_functions
   faas-cli up -f stack.yml
   ```

5. Access the services
   - API Gateway: http://localhost:8080
   - MinIO Console: http://localhost:9001
   - Kafka UI: http://localhost:8085

## System Architecture
```
User → API Gateway (Nginx) → MinIO (Storage) → Kafka (Message Queue) → OpenFaaS (Processing) → Results
```

## License
MIT License 