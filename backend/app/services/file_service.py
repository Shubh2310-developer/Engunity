"""
File service for handling file operations.
"""

import os
import shutil
import uuid
import boto3
from typing import BinaryIO, Optional
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

from app.config.settings import settings
from app.core.exceptions import FileStorageError

class FileService:
    """Service for file storage and retrieval."""
    
    def __init__(self):
        self.upload_path = Path(settings.upload_path)
        self.upload_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client for Supabase
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region
        )
    
    async def upload_file(self, file: BinaryIO, bucket: str, user_id: str, filename: Optional[str] = None) -> str:
        """
        Upload a file to Supabase S3 bucket.
        
        Args:
            file: File object to upload
            bucket: Bucket name (should be 'documents')
            user_id: User ID for organization
            filename: Optional original filename
            
        Returns:
            S3 object key/path
        """
        try:
            # Generate unique filename with optional original name preservation
            file_id = str(uuid.uuid4())
            if filename:
                # Keep original extension if provided
                ext = Path(filename).suffix
                s3_key = f"{user_id}/{file_id}{ext}"
            else:
                s3_key = f"{user_id}/{file_id}"
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file,
                settings.s3_bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': self._get_content_type(filename or s3_key)
                }
            )
            
            return s3_key
            
        except (ClientError, NoCredentialsError) as e:
            raise FileStorageError(f"Failed to upload file to S3: {str(e)}")
        except Exception as e:
            raise FileStorageError(f"Failed to upload file: {str(e)}")
    
    def _get_content_type(self, filename: str) -> str:
        """Get MIME type for file."""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.doc': 'application/msword'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    async def download_file(self, s3_key: str) -> bytes:
        """
        Download file from S3 storage.
        
        Args:
            s3_key: S3 object key/path
            
        Returns:
            File content as bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileStorageError(f"File not found: {s3_key}")
            raise FileStorageError(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise FileStorageError(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3 storage.
        
        Args:
            s3_key: S3 object key/path
            
        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            raise FileStorageError(f"Failed to delete file: {str(e)}")
        except Exception as e:
            raise FileStorageError(f"Failed to delete file: {str(e)}")
    
    async def get_file_info(self, s3_key: str) -> dict:
        """
        Get file information from S3.
        
        Args:
            s3_key: S3 object key/path
            
        Returns:
            File information dictionary
        """
        try:
            response = self.s3_client.head_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key
            )
            
            return {
                'size': response['ContentLength'],
                'modified': response['LastModified'].timestamp(),
                'content_type': response.get('ContentType', 'unknown'),
                'etag': response['ETag'],
                's3_key': s3_key
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileStorageError(f"File not found: {s3_key}")
            raise FileStorageError(f"Failed to get file info: {str(e)}")
        except Exception as e:
            raise FileStorageError(f"Failed to get file info: {str(e)}")
    
    async def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for file access.
        
        Args:
            s3_key: S3 object key/path
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.s3_bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            raise FileStorageError(f"Failed to generate presigned URL: {str(e)}")