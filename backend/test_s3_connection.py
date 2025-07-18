#!/usr/bin/env python3
"""
Test script to verify S3/Supabase bucket connectivity.
"""

import asyncio
import io
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Test configuration (using your provided credentials)
S3_ACCESS_KEY_ID = "daef80b0f4b050e45e7dedf3d993cf79"
S3_SECRET_ACCESS_KEY = "13abac6ee7f8414dc561c8306ee24bf4d05e93d5082462c165a1299af53f72f9"
S3_BUCKET_NAME = "documents"
S3_REGION = "us-east-1"
S3_ENDPOINT_URL = "https://ckrtquhwlvpmpgrfemmb.supabase.co/storage/v1/s3"

async def test_s3_connection():
    """Test S3 connection and basic operations."""
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            endpoint_url=S3_ENDPOINT_URL,
            region_name=S3_REGION
        )
        
        print("🔍 Testing S3 connection...")
        
        # Test 1: List buckets
        try:
            response = s3_client.list_buckets()
            print(f"✅ Successfully connected to S3")
            print(f"📦 Available buckets: {[bucket['Name'] for bucket in response['Buckets']]}")
        except Exception as e:
            print(f"❌ Failed to list buckets: {e}")
            return False
        
        # Test 2: Check if documents bucket exists
        try:
            s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"✅ Documents bucket '{S3_BUCKET_NAME}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"❌ Bucket '{S3_BUCKET_NAME}' does not exist")
                return False
            else:
                print(f"❌ Error checking bucket: {e}")
                return False
        
        # Test 3: Upload a test file
        test_content = b"This is a test file for S3 connectivity"
        test_key = "test/connectivity_test.txt"
        
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
            print(f"✅ Successfully uploaded test file: {test_key}")
        except Exception as e:
            print(f"❌ Failed to upload test file: {e}")
            return False
        
        # Test 4: Download the test file
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=test_key)
            downloaded_content = response['Body'].read()
            if downloaded_content == test_content:
                print(f"✅ Successfully downloaded and verified test file")
            else:
                print(f"❌ Downloaded content doesn't match uploaded content")
                return False
        except Exception as e:
            print(f"❌ Failed to download test file: {e}")
            return False
        
        # Test 5: Clean up test file
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=test_key)
            print(f"✅ Successfully deleted test file")
        except Exception as e:
            print(f"⚠️  Failed to delete test file: {e}")
        
        print("\n🎉 All S3 tests passed! Your Supabase S3 bucket is properly configured.")
        return True
        
    except (ClientError, NoCredentialsError) as e:
        print(f"❌ S3 connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_s3_connection())