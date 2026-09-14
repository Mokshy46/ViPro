# ViPro — Asynchronous Video Processing Platform

ViPro is a backend-focused video processing platform built with Django, RabbitMQ and Celery for asynchronous task processing, MinIO for object storage, PostgreSQL for persistence, and FFmpeg for media processing.

The platform separates video management from resource-intensive media.

## Architecture

```text
                         Client
                           │
                           ▼
                    ┌─────────────┐
                    │    Nginx    │
                    │ Reverse     │
                    │ Proxy       │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │ User Service│          │Video Service│
       │   Django    │          │   Django    │
       └──────┬──────┘          └──────┬──────┘
              │                        │
              │                        ▼
              │                 ┌─────────────┐
              │                 │   MinIO     │
              │                 │ Object      │
              │                 │ Storage     │
              │                 └─────────────┘
              │
              │                 Processing Job
              │                        │
              │                        ▼
              │                 ┌─────────────┐
              │                 │  RabbitMQ   │
              │                 │ Message     │
              │                 │ Broker      │
              │                 └──────┬──────┘
              │                        │
              │                        ▼
              │                 ┌─────────────┐
              │                 │   Celery    │
              │                 │   Worker    │
              │                 └──────┬──────┘
              │                        │
              │                        ▼
              │                 ┌─────────────┐
              │                 │   FFmpeg    │
              │                 │  Processing  │
              │                 └──────┬──────┘
              │                        │
              │                        ▼
              │                 ┌─────────────┐
              │                 │    MinIO    │
              │                 │   Outputs   │
              │                 └─────────────┘
              │
              └────────────── PostgreSQL

```
## How It Works

A video processing request follows this flow:
```
1. Client uploads video
          │
          ▼
2. Video Service
          │
          ├── Stores original video in MinIO
          │
          └── Stores metadata in PostgreSQL
          │
          ▼
3. Publishes processing job to RabbitMQ
          │
          ▼
4. Processing Service consumes the job
          │
          ▼
5. Celery schedules the processing task
          │
          ▼
6. Celery Worker executes FFmpeg
          │
          ├── Downloads source video from MinIO
          ├── Generates 720p output
          └── Generates thumbnail
          │
          ▼
7. Processed files uploaded to MinIO
          │
          ▼
8. Processing status published through RabbitMQ
          │
          ▼
9. Video Service updates PostgreSQL

```
The API does not need to wait for FFmpeg to finish. Video processing happens asynchronously in the background.


## Services
### User Service

Handles user-related functionality and authentication.
```
services/user-services/
```
### Video Service

Responsible for:

1. Video uploads
2. Video metadata
3. Processing status
4. Publishing processing jobs
5. Receiving processing results
6. Storing references to processed videos and thumbnails
```
services/video-services/
```

### Processing Service

Responsible for:

1. Consuming processing jobs
2. Scheduling Celery tasks
3. Downloading videos from MinIO
4. Running FFmpeg
5. Generating processed videos
6. Generating thumbnails
7. Uploading results to MinIO
8. Handling processing failures
9. Retrying transient failures
10. Publishing processing status
```
services/processing-services/
```

## Processing State

Each video moves through a processing lifecycle:
```
                 ┌──────────────┐
                 │   uploaded   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  processing  │
                 └──────┬───────┘
                        │
                 ┌──────┴──────┐
                 │             │
                 ▼             ▼
          ┌────────────┐  ┌────────────┐
          │ completed  │  │   failed   │
          └────────────┘  └────────────┘
```

## Failure Handling

The processing pipeline distinguishes between transient infrastructure failures and permanent processing failures.
Transient failures such as storage or network errors can be retried.
```
Processing Task
      │
      ▼
   Error
      │
      ▼
   Retry
      │
   ┌──┴──┐
   │     │
Success  Failure
   │     │
   ▼     ▼
Completed Failed
```
Processing failures such as invalid media input causing FFmpeg to fail are propagated back to the Video Service as a failed status.

## Concurrency

Celery workers allow multiple videos to be processed independently.

For example, with multiple worker processes:
```
                 Celery Worker
              ┌──────┼──────┬──────┐
              ▼      ▼      ▼      ▼
            Video  Video  Video  Video
              1      2      3      4
```
This allows CPU-intensive video processing to happen in the background without blocking the API service.

## Technology Stack
### Backend
- Python
- Django
- Django REST Framework
- PostgreSQL
### Asynchronous Processing
- Celery
- RabbitMQ
- Pika
### Video Processing
- FFmpeg
### Object Storage
- MinIO
- S3-compatible object storage
- boto3
- django-storages
### Infrastructure
- Docker
- Docker Compose
- Nginx
- Gunicorn
- systemd

## Infrastructure

Infrastructure dependencies are defined using Docker Compose.
```
Docker Compose
│
├── PostgreSQL
├── RabbitMQ
└── MinIO
```
Start the infrastructure:
```
docker compose -f infrastructure/docker-compose.yml up -d
```
Check the containers:
```
docker compose -f infrastructure/docker-compose.yml ps
```
Stop the infrastructure:
```
docker compose -f infrastructure/docker-compose.yml down
```

## Environment Configuration

Copy the example environment file:
```
cp infrastructure/.env.example infrastructure/.env
```
Update the values in infrastructure/.env before starting the infrastructure.

Real credentials are intentionally excluded from the repository.

Service-specific .env files are also excluded from Git.

## PostgreSQL

PostgreSQL runs inside Docker and is exposed locally on port 5433.
```
Host:      localhost
Port:      5433
Container: 5432
```
The infrastructure automatically creates the databases and users required by the services when PostgreSQL initializes a new empty volume.
```
PostgreSQL
│
├── video_service
│   └── video_user
│
├── user_service
│   └── user_service_user
│
└── processing_service
    └── processing_service_user
```
The initialization script is located at:
```
infrastructure/postgres/init/01-init.sh
```
The script runs automatically when PostgreSQL starts with a new empty data directory.

## MinIO

MinIO provides S3-compatible object storage for video files and generated outputs.

Example storage structure:
```
videos/
│
├── input/
│   └── <video-id>.<extension>
│
├── output/
│   └── <video-id>_720p.mp4
│
└── thumbnails/
    └── <video-id>.jpg
```
Large video files are stored in object storage instead of PostgreSQL.

PostgreSQL stores the associated metadata and object references.

## RabbitMQ

RabbitMQ acts as the message broker between services.

The Video Service publishes processing jobs:
```
Video Service
      │
      ▼
 RabbitMQ
      │
      ▼
Processing Service
```
Processing status is also communicated asynchronously:
```
Processing Service
      │
      ▼
 RabbitMQ
      │
      ▼
Video Service
      │
      ▼
PostgreSQL
```
RabbitMQ is also used as the Celery broker.

## Celery

Celery handles background execution of video-processing tasks.
```
RabbitMQ
    │
    ▼
Celery
    │
    ▼
Worker
    │
    ▼
FFmpeg
```
This keeps CPU-intensive processing separate from the HTTP request/response cycle.

## Nginx and Gunicorn

Nginx acts as the public HTTP entry point.
```
Client
  │
  ▼
Nginx :80
  │
  ├── /api/video/ ──► Video Service :8000
  │
  └── /api/auth/  ──► User Service :8001
```
Django applications run behind Gunicorn.

The application services are managed using systemd on the development machine.

## Project Structure
```
ViPro/
│
├── infrastructure/
│   ├── docker-compose.yml
│   ├── .env.example
│   │
│   └── postgres/
│       └── init/
│           └── 01-init.sh
│
├── services/
│   │
│   ├── user-services/
│   │   └── core/
│   │
│   ├── video-services/
│   │   └── core/
│   │
│   └── processing-services/
│       └── core/
│
└── README.md
```

## Running Django Services

After starting the infrastructure, run migrations for each service.

### Video Service
```
cd services/video-services/core
python manage.py migrate
```
### User Service
```
cd services/user-services/core
python manage.py migrate
```
### Processing Service
```
cd services/processing-services/core
python manage.py migrate
```

## Running with Gunicorn

Example Video Service:
```
gunicorn --workers 3 --bind 127.0.0.1:8000 core.wsgi:application
```
Example User Service:
```
gunicorn --workers 3 --bind 127.0.0.1:8001 core.wsgi:application
```
## Running the Celery Worker

From the Processing Service:
```
celery -A core worker --loglevel=info
```

## API
### Video API
```
/api/video/
```
### Authentication API
```
/api/auth/
```
The Video Service provides video upload functionality and exposes the video's processing state and generated output references.

## Engineering Highlights
### Asynchronous Video Processing

Long-running FFmpeg operations are moved away from the HTTP request cycle using RabbitMQ and Celery.

### Service Separation

User management, video management, and media processing are separated into independent Django services.

### Object Storage

Video files are stored in MinIO using an S3-compatible interface while PostgreSQL stores application metadata.

### Retry Handling

Transient storage and processing infrastructure failures are retried before the task is ultimately marked as failed.

### Concurrent Processing

Celery workers allow multiple independent video-processing jobs to execute concurrently.

### Reproducible Infrastructure

Docker Compose defines the infrastructure dependencies and automatically initializes the required PostgreSQL databases and users on a fresh volume.

## Future Improvements
- Dead-letter queues
- Idempotent processing
- Processing progress tracking
- Multiple output resolutions
- Video metadata extraction
- Horizontal Celery worker scaling
- Centralized logging
- Distributed tracing
- Automated CI/CD
- Containerized application services
- Production object-storage configuration
## Project Status

ViPro V3 is an actively developed backend project focused on asynchronous video processing, service separation, background task execution, and reproducible infrastructure.
