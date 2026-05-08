from __future__ import annotations

from uuid import uuid4

import boto3
import pytest
from testcontainers.localstack import LocalStackContainer

from smart_service.adapter.outbound.s3_asset_reader import S3AssetReader, S3AssetReadError
from smart_service.domain.model import Asset, ContentType

BUCKET = "fiap-secure-systems-assets"


@pytest.fixture(scope="module")
def localstack():
    with LocalStackContainer(image="localstack/localstack:3.5").with_services("s3") as ls:
        yield ls


@pytest.fixture()
def s3_client(localstack):
    cli = boto3.client(
        "s3",
        endpoint_url=localstack.get_url(),
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    try:
        cli.create_bucket(Bucket=BUCKET)
    except cli.exceptions.BucketAlreadyOwnedByYou:
        pass
    yield cli


@pytest.mark.integration
def test_round_trip(localstack, s3_client):
    s3_client.put_object(Bucket=BUCKET, Key="sessions/abc/img.png", Body=b"bytes-here")

    reader = S3AssetReader(
        endpoint_url=localstack.get_url(),
        region="us-east-1",
        access_key="test",
        secret_key="test",
        bucket=BUCKET,
    )
    asset = Asset(
        asset_id=uuid4(),
        s3_key="sessions/abc/img.png",
        content_type=ContentType.IMAGE_PNG,
        filename="img.png",
        size_bytes=10,
    )
    assert reader.read(asset) == b"bytes-here"


@pytest.mark.integration
def test_missing_key_raises(localstack):
    reader = S3AssetReader(
        endpoint_url=localstack.get_url(),
        region="us-east-1",
        access_key="test",
        secret_key="test",
        bucket=BUCKET,
    )
    asset = Asset(
        asset_id=uuid4(),
        s3_key="sessions/abc/missing.png",
        content_type=ContentType.IMAGE_PNG,
        filename="missing.png",
        size_bytes=10,
    )
    with pytest.raises(S3AssetReadError):
        reader.read(asset)
