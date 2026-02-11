# Doctor Analyzer

A full-stack web application for analyzing patient videos, documents, and text for emotional and sentiment analysis using AWS services.

## Features

- **Video Upload & Analysis**: Upload patient consultation videos for emotion detection
- **Real-time Emotion Overlay**: See emotions detected in real-time overlaid on the video
- **Audio Transcription**: Automatic audio transcription with sentiment analysis
- **Document Analysis**: Upload PDF documents for text extraction and sentiment analysis
- **Clinical Indicators**: Automated detection of discomfort, depression, anxiety, and fear
- **WebSocket Streaming**: Real-time updates as analysis progresses

## Technology Stack

### Frontend
- React 18 with TypeScript
- TailwindCSS for styling
- Vite for build tooling
- WebSocket for real-time updates

### Backend
- Python 3.11 with FastAPI
- WebSocket support for streaming
- Async/await patterns throughout

### AWS Services
- **S3**: File storage for videos, documents, and results
- **Rekognition**: Video face and emotion detection
- **Transcribe**: Audio to text conversion
- **Comprehend**: Sentiment analysis and entity detection
- **Textract**: PDF text extraction

## Prerequisites

1. **AWS Account** with access to:
   - S3
   - Rekognition
   - Transcribe
   - Comprehend
   - Textract

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/video` | Upload video file |
| POST | `/api/upload/documents` | Upload PDF documents |
| POST | `/api/upload/text` | Add text input |
| POST | `/api/analysis/{session_id}/start` | Start analysis |
| GET | `/api/analysis/{session_id}/status` | Get analysis status |
| GET | `/api/analysis/{session_id}/results` | Get complete results |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{session_id}` | Get session details |
| WS | `/ws/analysis/{session_id}` | Real-time streaming |

## WebSocket Messages

### Server to Client

- `status_update`: Analysis status changes with progress
- `emotion_update`: Real-time emotion detections
- `transcription_update`: Transcription segments
- `sentiment_update`: Sentiment analysis results
- `complete`: Final aggregated results
- `error`: Error messages

### Client to Server

- `{"action": "get_status"}`: Request current status
- `{"action": "ping"}`: Keep connection alive

## Project Structure

```
doctor-analyzer/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config/                 # Configuration
│   ├── domain/                 # Domain models
│   ├── infrastructure/         # AWS clients, WebSocket
│   ├── services/               # Business logic
│   └── api/                    # Routes and endpoints
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── services/           # API client
│   │   └── types/              # TypeScript types
│   └── ...
├── docker-compose.yml
└── README.md
```

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
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::doctor-analyzer-uploads",
        "arn:aws:s3:::doctor-analyzer-uploads/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:StartFaceDetection",
        "rekognition:GetFaceDetection",
        "rekognition:DetectFaces"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob",
        "transcribe:DeleteTranscriptionJob"
      ],
      "Resource": "*"
    },
    {
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
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection",
        "textract:DetectDocumentText"
      ],
      "Resource": "*"
    }
  ]
}
```

## Usage

1. **Upload Video**: Drag and drop or select a patient consultation video
2. **Add Documents** (Optional): Upload relevant PDF documents
3. **Add Notes** (Optional): Enter additional observations
4. **Start Analysis**: Click to begin processing
5. **View Results**: Watch real-time emotion overlay and analysis results

## License

This project is for educational and research purposes.
