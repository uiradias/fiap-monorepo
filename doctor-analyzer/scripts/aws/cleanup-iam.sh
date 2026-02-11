#!/bin/bash

# Doctor Analyzer - AWS IAM Cleanup Script
# This script removes all IAM resources created by setup-iam.sh

set -e

# Configuration
POLICY_NAME="DoctorAnalyzerPolicy"
USER_NAME="doctor-analyzer-user"
ROLE_NAME="DoctorAnalyzerRekognitionRole"
S3_BUCKET="doctor-analyzer-uploads"

echo "=========================================="
echo "Doctor Analyzer - AWS IAM Cleanup"
echo "=========================================="
echo ""
echo "This will delete the following resources:"
echo "  - IAM User: $USER_NAME"
echo "  - IAM Policy: $POLICY_NAME"
echo "  - IAM Role: $ROLE_NAME"
echo "  - S3 Bucket: $S3_BUCKET (optional)"
echo ""
echo "Are you sure you want to continue? (y/N)"
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"

# Step 1: Delete access keys and detach policies from user
echo ""
echo "Step 1: Cleaning up IAM user..."
if aws iam get-user --user-name "$USER_NAME" 2>/dev/null; then
    # Delete access keys
    KEYS=$(aws iam list-access-keys --user-name "$USER_NAME" \
        --query 'AccessKeyMetadata[].AccessKeyId' --output text)
    for key in $KEYS; do
        echo "  Deleting access key: $key"
        aws iam delete-access-key --user-name "$USER_NAME" --access-key-id "$key"
    done

    # Detach policies
    POLICIES=$(aws iam list-attached-user-policies --user-name "$USER_NAME" \
        --query 'AttachedPolicies[].PolicyArn' --output text)
    for policy in $POLICIES; do
        echo "  Detaching policy: $policy"
        aws iam detach-user-policy --user-name "$USER_NAME" --policy-arn "$policy"
    done

    # Delete user
    aws iam delete-user --user-name "$USER_NAME"
    echo "  Deleted user: $USER_NAME"
else
    echo "  User '$USER_NAME' not found."
fi

# Step 2: Delete IAM policy
echo ""
echo "Step 2: Deleting IAM policy..."
if aws iam get-policy --policy-arn "$POLICY_ARN" 2>/dev/null; then
    # Delete all non-default versions
    VERSIONS=$(aws iam list-policy-versions --policy-arn "$POLICY_ARN" \
        --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text)
    for version in $VERSIONS; do
        echo "  Deleting policy version: $version"
        aws iam delete-policy-version --policy-arn "$POLICY_ARN" --version-id "$version"
    done

    # Delete policy
    aws iam delete-policy --policy-arn "$POLICY_ARN"
    echo "  Deleted policy: $POLICY_NAME"
else
    echo "  Policy '$POLICY_NAME' not found."
fi

# Step 3: Delete Rekognition role
echo ""
echo "Step 3: Deleting Rekognition role..."
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    # Delete inline policies
    INLINE_POLICIES=$(aws iam list-role-policies --role-name "$ROLE_NAME" \
        --query 'PolicyNames' --output text)
    for policy in $INLINE_POLICIES; do
        echo "  Deleting inline policy: $policy"
        aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "$policy"
    done

    # Detach managed policies
    MANAGED_POLICIES=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" \
        --query 'AttachedPolicies[].PolicyArn' --output text)
    for policy in $MANAGED_POLICIES; do
        echo "  Detaching policy: $policy"
        aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn "$policy"
    done

    # Delete role
    aws iam delete-role --role-name "$ROLE_NAME"
    echo "  Deleted role: $ROLE_NAME"
else
    echo "  Role '$ROLE_NAME' not found."
fi

# Step 4: Delete S3 bucket (optional)
echo ""
echo "Step 4: Delete S3 bucket? (y/N)"
read -r DELETE_BUCKET

if [[ "$DELETE_BUCKET" =~ ^[Yy]$ ]]; then
    if aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
        echo "  Emptying bucket..."
        aws s3 rm "s3://$S3_BUCKET" --recursive
        echo "  Deleting bucket..."
        aws s3api delete-bucket --bucket "$S3_BUCKET"
        echo "  Deleted bucket: $S3_BUCKET"
    else
        echo "  Bucket '$S3_BUCKET' not found."
    fi
else
    echo "  Skipping S3 bucket deletion."
fi

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
