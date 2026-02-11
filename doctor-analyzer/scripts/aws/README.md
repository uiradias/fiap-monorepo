# AWS Setup Scripts

This folder contains scripts and templates to set up the required AWS IAM permissions and infrastructure for the Doctor Analyzer application.

## Quick Start

### Shell Script (Recommended for development)

```bash
# Make the script executable
chmod +x setup-iam.sh

# Run the setup script
./setup-iam.sh
```

This will:
1. Create an S3 bucket for uploads
2. Create an IAM policy with required permissions
3. Create an IAM user
4. Generate access keys
5. Create a Rekognition role for async video analysis
6. Save credentials to `.env` file

## Files

| File | Description |
|------|-------------|
| `setup-iam.sh` | Shell script for manual IAM setup |
| `cleanup-iam.sh` | Shell script to remove all created resources |
| `iam-policy.json` | IAM policy document with required permissions |
| `rekognition-trust-policy.json` | Trust policy for Rekognition role |
| `rekognition-role-policy.json` | Inline policy for Rekognition role |

## Required Permissions

The IAM policy grants access to:

### S3
- `s3:PutObject` - Upload files
- `s3:GetObject` - Download files
- `s3:DeleteObject` - Delete files
- `s3:ListBucket` - List bucket contents

### Rekognition
- `rekognition:StartFaceDetection` - Start video analysis
- `rekognition:GetFaceDetection` - Get analysis results
- `rekognition:DetectFaces` - Detect faces in images

### Transcribe
- `transcribe:StartTranscriptionJob` - Start audio transcription
- `transcribe:GetTranscriptionJob` - Get transcription status/results
- `transcribe:DeleteTranscriptionJob` - Clean up jobs

### Comprehend
- `comprehend:DetectSentiment` - Analyze sentiment
- `comprehend:BatchDetectSentiment` - Batch sentiment analysis
- `comprehend:DetectKeyPhrases` - Extract key phrases
- `comprehend:DetectEntities` - Detect entities
- `comprehend:DetectDominantLanguage` - Detect language

### Textract
- `textract:StartDocumentTextDetection` - Start PDF text extraction
- `textract:GetDocumentTextDetection` - Get extraction results
- `textract:DetectDocumentText` - Sync text detection

## Environment Variables

After running setup, the following environment variables will be configured:

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=doctor-analyzer-uploads
REKOGNITION_ROLE_ARN=arn:aws:iam::...
SNS_TOPIC_ARN=arn:aws:sns:...
```

## Cleanup

### Shell Script Setup

```bash
chmod +x cleanup-iam.sh
./cleanup-iam.sh
```

## Troubleshooting

### Permission Denied

Ensure your AWS CLI has admin permissions to create IAM resources:

```bash
aws iam get-user  # Should return your user info
aws iam list-policies --scope Local  # Should list policies
```

### Bucket Already Exists

S3 bucket names are globally unique. If the bucket name is taken:

```bash
# Use a different bucket name
export S3_BUCKET="doctor-analyzer-uploads-$(date +%s)"
./setup-iam.sh
```
