# Doctor Analyzer

A full-stack web application for analyzing patient consultation videos using AWS AI/ML services. It performs real-time emotion detection, audio transcription, sentiment analysis, injury detection, and AI-powered clinical summarization.

## Features

- **Patient Management**: Create and manage patient records with codenames for privacy
- **Video Upload & Analysis**: Upload patient consultation videos for multi-modal analysis
- **Real-time Emotion Overlay**: Bounding boxes with emotion labels overlaid on the video during analysis
- **Audio Transcription**: Automatic speech-to-text with segment-level timing and pagination
- **Sentiment Analysis**: Overall and per-segment sentiment scoring via AWS Comprehend
- **Injury Detection**: Content moderation via Rekognition, enhanced with AI clinical reasoning via Bedrock
- **AI Clinical Summary**: Cross-referenced multi-modal aggregation with risk assessment and recommendations
- **Clinical Indicators**: Automated detection of discomfort, depression, anxiety, and fear
- **WebSocket Streaming**: Real-time updates as each pipeline stage completes
- **Breadcrumb Navigation**: Hierarchical breadcrumb navigation across all pages

## Technology Stack

### Frontend
- React 18 with TypeScript
- TailwindCSS for styling
- Vite for build tooling
- lucide-react for icons
- WebSocket for real-time updates

### Backend
- Python 3.11 with FastAPI
- WebSocket support for streaming
- Async/await patterns throughout
- PostgreSQL 16 with SQLAlchemy 2.0 (async) and Alembic migrations

### AWS Services
- **S3**: File storage for videos and analysis results
- **Rekognition**: Video face/emotion detection and content moderation
- **Transcribe**: Audio to text conversion with speaker labels
- **Comprehend**: Sentiment analysis, key phrase extraction, and entity detection
- **Bedrock**: LLM-powered clinical interpretation and multi-modal aggregation (Claude 3 Sonnet)
- **Textract**: PDF text extraction
- **PostgreSQL**: Patient and session data persistence (via SQLAlchemy async + Alembic migrations)

## Prerequisites

1. **AWS Account** with access to:
   - S3
   - Rekognition
   - Transcribe
   - Comprehend
   - Bedrock (with Claude 3 Sonnet model access)
   - Textract
   - PostgreSQL (or any async-compatible database)

2. **Docker & Docker Compose** installed

3. **AWS Credentials** configured

## Quick Start

### 1. Clone and navigate to the project

```bash
cd doctor-analyzer
```

### 2. Configure environment variables

```bash
# Copy example env file
cp .env.example .env

# Edit with your AWS credentials
nano .env
```

Required environment variables:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=doctor-analyzer-uploads
```

Optional environment variables:
```
BEDROCK_MODEL_ID=us.anthropic.claude-3-sonnet-20240229-v1:0
REKOGNITION_ROLE_ARN=
SNS_TOPIC_ARN=
CORS_ORIGINS=http://localhost:5173
DEBUG=true
```

### 3. Create S3 bucket

```bash
aws s3 mb s3://doctor-analyzer-uploads --region us-east-1
```

### 4. Start with Docker Compose

```bash
docker-compose up --build
```

### 5. Access the application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Endpoints

### Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/patients` | Create a new patient |
| GET | `/api/patients` | List all patients |
| GET | `/api/patients/{patient_id}` | Get patient details |
| DELETE | `/api/patients/{patient_id}` | Delete patient and associated sessions |

### Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/video` | Upload video file (MP4, MOV, AVI, WebM) |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analysis/{session_id}/start` | Start analysis pipeline |
| GET | `/api/analysis/{session_id}/status` | Get analysis status |
| GET | `/api/analysis/{session_id}/results` | Get complete results (loads from S3) |

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List sessions (optional `?patient_id=` filter) |
| GET | `/api/sessions/{session_id}` | Get session details |
| GET | `/api/sessions/{session_id}/full` | Get full session with all results |
| GET | `/api/sessions/{session_id}/video-url` | Get presigned video playback URL |
| GET | `/api/sessions/{session_id}/face-detections` | Get emotion detection data |
| DELETE | `/api/sessions/{session_id}` | Delete session |

### WebSocket

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/{session_id}` | Real-time analysis streaming |

## WebSocket Messages

### Server to Client

- `status_update`: Analysis status changes with progress percentage
- `emotion_update`: Real-time emotion detections with bounding boxes
- `transcription_update`: Transcription segments with timestamps
- `complete`: Final aggregated results
- `error`: Error messages

### Client to Server

- `{"action": "get_status"}`: Request current status
- `{"action": "ping"}`: Keep connection alive

## Analysis Pipeline

The analysis runs as a background task with the following stages:

1. **Video Analysis** — Rekognition face detection with emotion scoring, streamed via WebSocket
2. **Injury Check** — Rekognition content moderation for injury-related signals
3. **Audio Analysis** — Transcribe for speech-to-text, Comprehend for sentiment analysis
4. **Bedrock Enhancement** — AI-enhanced injury interpretation and transcript analysis for verbal indicators
5. **Bedrock Aggregation** — Cross-referenced multi-modal clinical summary with risk level and recommendations
6. **Results Aggregation** — Clinical indicator generation and final report saved to S3

## Project Structure

```
doctor-analyzer/
├── backend/
│   ├── main.py                          # FastAPI entry point
│   ├── config/                          # Configuration
│   ├── domain/
│   │   ├── analysis.py                  # Analysis domain models (status, results, injury check)
│   │   ├── patient.py                   # Patient domain model
│   │   └── session.py                   # Session store interface
│   ├── infrastructure/
│   │   ├── aws/
│   │   │   ├── s3_client.py             # S3 file operations
│   │   │   ├── rekognition_client.py    # Face detection & content moderation
│   │   │   ├── transcribe_client.py     # Speech-to-text
│   │   │   ├── comprehend_client.py     # Sentiment & NLP analysis
│   │   │   ├── bedrock_client.py        # LLM model invocation
│   │   │   └── textract_client.py       # Document text extraction
│   │   ├── persistence/
│   │   │   └── session_repository.py    # DynamoDB session persistence
│   │   └── websocket/
│   │       └── connection_manager.py    # WebSocket connection management
│   ├── services/
│   │   ├── upload_service.py            # Video upload orchestration
│   │   ├── video_analysis_service.py    # Rekognition emotion analysis
│   │   ├── audio_analysis_service.py    # Transcription & sentiment
│   │   ├── injury_check_service.py      # Content moderation & injury detection
│   │   ├── bedrock_analysis_service.py  # AI-enhanced analysis & aggregation
│   │   ├── aggregation_service.py       # Results compilation & report generation
│   │   ├── patient_service.py           # Patient CRUD
│   │   └── prompts/
│   │       ├── injury_prompts.py        # LLM prompts for injury analysis
│   │       └── aggregation_prompts.py   # LLM prompts for clinical aggregation
│   └── api/
│       ├── routes/
│       │   ├── analysis.py              # Analysis endpoints
│       │   ├── upload.py                # Upload endpoints
│       │   ├── sessions.py              # Session endpoints
│       │   └── patients.py              # Patient endpoints
│       └── websocket/
│           └── analysis_ws.py           # WebSocket handler
├── frontend/
│   ├── src/
│   │   ├── App.tsx                      # Routes & AnalysisPage
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Breadcrumb.tsx       # Breadcrumb navigation with back arrow
│   │   │   │   ├── Header.tsx           # App header
│   │   │   │   └── MainLayout.tsx       # Root layout wrapper
│   │   │   ├── analysis/
│   │   │   │   └── AnalysisPanel.tsx    # Status, transcription, injury, clinical indicators, AI summary
│   │   │   ├── patients/
│   │   │   │   ├── PatientList.tsx      # Patient management table
│   │   │   │   └── PatientSessions.tsx  # Paginated session list for a patient
│   │   │   ├── sessions/
│   │   │   │   └── SessionResults.tsx   # Completed session results page
│   │   │   ├── upload/
│   │   │   │   └── UploadZone.tsx       # Drag-and-drop video upload
│   │   │   └── video/
│   │   │       ├── VideoPlayer.tsx      # Video playback with controls
│   │   │       └── VideoOverlay.tsx     # Real-time emotion bounding box overlay
│   │   ├── hooks/
│   │   │   ├── useAnalysis.ts           # Analysis state management
│   │   │   └── useWebSocket.ts          # WebSocket connection hook
│   │   ├── services/
│   │   │   └── api.ts                   # Axios HTTP client
│   │   └── types/
│   │       └── analysis.ts              # TypeScript type definitions
│   └── ...
├── docker-compose.yml
└── README.md
```

## Frontend Routes

| Path | Page | Description |
|------|------|-------------|
| `/` | Home | Patient list with create/manage functionality |
| `/patients/:patientId/sessions` | Patient Sessions | Paginated session list for a patient |
| `/patients/:patientId/sessions/:sessionId` | Session Results | Completed session with video, transcription, and all analysis results |
| `/patients/:patientId/upload` | New Analysis | Video upload with auto-triggered analysis and real-time progress |

## Clinical Indicators

The system detects the following emotional indicators:

| Indicator | Detection Method |
|-----------|-----------------|
| **Discomfort** | 40% disgusted + 30% confused + 30% sad |
| **Anxiety** | 70% fear + 30% surprised |
| **Depression** | 60% sad + 20% (1-happy) + 20% calm |
| **Fear** | Direct from Rekognition |

## AWS Setup Notes

### IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:HeadObject"
      ],
      "Resource": [
        "arn:aws:s3:::doctor-analyzer-uploads",
        "arn:aws:s3:::doctor-analyzer-uploads/*"
      ]
    },
    {
      "Sid": "RekognitionAccess",
      "Effect": "Allow",
      "Action": [
        "rekognition:StartFaceDetection",
        "rekognition:GetFaceDetection",
        "rekognition:DetectFaces",
        "rekognition:StartContentModeration",
        "rekognition:GetContentModeration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TranscribeAccess",
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob",
        "transcribe:DeleteTranscriptionJob"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ComprehendAccess",
      "Effect": "Allow",
      "Action": [
        "comprehend:DetectSentiment",
        "comprehend:BatchDetectSentiment",
        "comprehend:DetectKeyPhrases",
        "comprehend:DetectEntities",
        "comprehend:DetectDominantLanguage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Sid": "TextractAccess",
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection",
        "textract:DetectDocumentText",
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis"
      ],
      "Resource": "*"
    }
  ]
}
```

> **Note:** Patient and session data is stored in PostgreSQL (not an AWS database service). No AWS database IAM permissions are required.

## Usage

1. **Create Patient**: Add a patient with a codename for privacy
2. **Upload Video**: Navigate to the patient and upload a consultation video
3. **Automatic Analysis**: Analysis starts automatically after upload — follow progress via the pipeline stepper
4. **View Results**: Review emotion overlay, transcription, injury detection, clinical indicators, and AI clinical summary
5. **Review Past Sessions**: Navigate to any patient to view paginated session history and detailed results

## License

This project is for educational and research purposes.
