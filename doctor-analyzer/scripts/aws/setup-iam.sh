#!/bin/bash

# Doctor Analyzer - AWS IAM Setup Script
# This script creates all necessary IAM resources for the application

set -e

# Parse arguments
AWS_PROFILE_ARG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE_ARG="--profile $2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--profile <aws-profile-name>]"
            exit 1
            ;;
    esac
done

# Configuration
POLICY_NAME="DoctorAnalyzerPolicy"
USER_NAME="doctor-analyzer-user"
ROLE_NAME="DoctorAnalyzerRekognitionRole"
S3_BUCKET="doctor-analyzer-uploads"
AWS_REGION="${AWS_REGION:-us-east-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Doctor Analyzer - AWS IAM Setup"
echo "=========================================="
echo ""
echo "Region: $AWS_REGION"
echo "Bucket: $S3_BUCKET"
if [ -n "$AWS_PROFILE_ARG" ]; then
    echo "Profile: ${AWS_PROFILE_ARG#--profile }"
fi
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity $AWS_PROFILE_ARG &> /dev/null; then
    echo "Error: AWS credentials are not configured."
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_ARG --query Account --output text)
echo "AWS Account ID: $ACCOUNT_ID"
echo ""

# Step 1: Create S3 Bucket
echo "Step 1: Creating S3 bucket..."
if aws s3api head-bucket $AWS_PROFILE_ARG --bucket "$S3_BUCKET" 2>/dev/null; then
    echo "  Bucket '$S3_BUCKET' already exists."
else
    aws s3api create-bucket $AWS_PROFILE_ARG \
        --bucket "$S3_BUCKET" \
        --region "$AWS_REGION" \
        $([ "$AWS_REGION" != "us-east-1" ] && echo "--create-bucket-configuration LocationConstraint=$AWS_REGION")
    echo "  Created bucket: $S3_BUCKET"
fi

# Enable CORS on S3 bucket for frontend access
echo "  Configuring CORS..."
aws s3api put-bucket-cors $AWS_PROFILE_ARG --bucket "$S3_BUCKET" --cors-configuration '{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
            "AllowedOrigins": ["http://localhost:5173", "http://localhost:3000"],
            "ExposeHeaders": ["ETag"]
        }
    ]
}'
echo "  CORS configured."
echo ""

# Step 2: Create IAM Policy
echo "Step 2: Creating IAM policy..."

# Update policy with actual bucket name
POLICY_DOCUMENT=$(cat "$SCRIPT_DIR/iam-policy.json" | sed "s/doctor-analyzer-uploads/$S3_BUCKET/g")

POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"

if aws iam get-policy $AWS_PROFILE_ARG --policy-arn "$POLICY_ARN" 2>/dev/null; then
    echo "  Policy '$POLICY_NAME' already exists. Updating..."
    # Create new version
    aws iam create-policy-version $AWS_PROFILE_ARG \
        --policy-arn "$POLICY_ARN" \
        --policy-document "$POLICY_DOCUMENT" \
        --set-as-default

    # Delete old versions (keep max 5)
    OLD_VERSIONS=$(aws iam list-policy-versions $AWS_PROFILE_ARG --policy-arn "$POLICY_ARN" \
        --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text)
    for version in $OLD_VERSIONS; do
        aws iam delete-policy-version $AWS_PROFILE_ARG --policy-arn "$POLICY_ARN" --version-id "$version" 2>/dev/null || true
    done
else
    aws iam create-policy $AWS_PROFILE_ARG \
        --policy-name "$POLICY_NAME" \
        --policy-document "$POLICY_DOCUMENT" \
        --description "Policy for Doctor Analyzer application"
    echo "  Created policy: $POLICY_NAME"
fi
echo ""

# Step 3: Create IAM User
echo "Step 3: Creating IAM user..."
if aws iam get-user $AWS_PROFILE_ARG --user-name "$USER_NAME" 2>/dev/null; then
    echo "  User '$USER_NAME' already exists."
else
    aws iam create-user $AWS_PROFILE_ARG --user-name "$USER_NAME"
    echo "  Created user: $USER_NAME"
fi

# Attach policy to user
echo "  Attaching policy to user..."
aws iam attach-user-policy $AWS_PROFILE_ARG \
    --user-name "$USER_NAME" \
    --policy-arn "$POLICY_ARN"
echo ""

# Step 4: Create access keys
echo "Step 4: Creating access keys..."
echo "  Do you want to create new access keys? (y/N)"
read -r CREATE_KEYS

if [[ "$CREATE_KEYS" =~ ^[Yy]$ ]]; then
    # Delete existing keys
    EXISTING_KEYS=$(aws iam list-access-keys $AWS_PROFILE_ARG --user-name "$USER_NAME" \
        --query 'AccessKeyMetadata[].AccessKeyId' --output text)
    for key in $EXISTING_KEYS; do
        echo "  Deleting existing key: $key"
        aws iam delete-access-key $AWS_PROFILE_ARG --user-name "$USER_NAME" --access-key-id "$key"
    done

    # Create new keys
    CREDENTIALS=$(aws iam create-access-key $AWS_PROFILE_ARG --user-name "$USER_NAME")
    ACCESS_KEY=$(echo "$CREDENTIALS" | grep -o '"AccessKeyId": "[^"]*' | cut -d'"' -f4)
    SECRET_KEY=$(echo "$CREDENTIALS" | grep -o '"SecretAccessKey": "[^"]*' | cut -d'"' -f4)

    echo ""
    echo "=========================================="
    echo "ACCESS CREDENTIALS (save these securely!)"
    echo "=========================================="
    echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY"
    echo "AWS_SECRET_ACCESS_KEY=$SECRET_KEY"
    echo "=========================================="
    echo ""

    # Save to .env file
    ENV_FILE="$SCRIPT_DIR/../../.env"
    echo "  Saving to .env file..."
    cat > "$ENV_FILE" << EOF
# AWS Configuration
AWS_REGION=$AWS_REGION
AWS_ACCESS_KEY_ID=$ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$SECRET_KEY
S3_BUCKET=$S3_BUCKET

# Optional: For Rekognition async notifications
REKOGNITION_ROLE_ARN=arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME
SNS_TOPIC_ARN=

# Application Settings
CORS_ORIGINS=http://localhost:5173
DEBUG=true
EOF
    echo "  Credentials saved to .env"
fi
echo ""

# Step 5: Create Rekognition Role (optional, for async video analysis)
echo "Step 5: Creating Rekognition role (for async video analysis)..."
if aws iam get-role $AWS_PROFILE_ARG --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "  Role '$ROLE_NAME' already exists."
else
    aws iam create-role $AWS_PROFILE_ARG \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://"$SCRIPT_DIR/rekognition-trust-policy.json" \
        --description "Role for Rekognition to access S3 and SNS"
    echo "  Created role: $ROLE_NAME"

    # Create and attach inline policy
    ROLE_POLICY=$(cat "$SCRIPT_DIR/rekognition-role-policy.json" | sed "s/doctor-analyzer-uploads/$S3_BUCKET/g")
    aws iam put-role-policy $AWS_PROFILE_ARG \
        --role-name "$ROLE_NAME" \
        --policy-name "RekognitionAccessPolicy" \
        --policy-document "$ROLE_POLICY"
    echo "  Attached policy to role."
fi
echo ""

# Summary
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Resources created:"
echo "  - S3 Bucket: $S3_BUCKET"
echo "  - IAM Policy: $POLICY_NAME"
echo "  - IAM User: $USER_NAME"
echo "  - IAM Role: $ROLE_NAME"
echo ""
echo "Next steps:"
echo "  1. Review the .env file in the project root"
echo "  2. Run: docker-compose up --build"
echo "  3. Access the app at http://localhost:5173"
echo ""
