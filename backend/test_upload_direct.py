#!/usr/bin/env python3
"""
Test direct document upload to verify S3 integration without authentication.
"""

import asyncio
import io
import uuid
from fastapi import UploadFile
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate

async def test_direct_upload():
    """Test document upload without authentication."""
    
    # Create test document content
    test_content = b"""# Test Document

This is a test document to verify that S3 upload is working correctly.

## Features:
- Document upload to Supabase S3 bucket
- File storage with proper organization
- Content type handling

The document should be uploaded to the documents bucket under the user's folder.
"""
    
    # Create a mock UploadFile
    test_file = io.BytesIO(test_content)
    
    # Create document data
    document_data = DocumentCreate(
        title="Test Document Upload",
        description="Testing S3 integration",
        tags=["test", "s3", "upload"],
        filename="test_document.md",
        file_type="text/markdown",
        file_size=len(test_content)
    )
    
    # Create document service
    document_service = DocumentService()
    
    try:
        # Test file upload directly to S3
        s3_key = await document_service.file_service.upload_file(
            file=test_file,
            bucket="documents", 
            user_id="test-user-123",
            filename="test_document.md"
        )
        
        print(f"✅ File uploaded to S3: {s3_key}")
        
        # Test file download
        downloaded_content = await document_service.file_service.download_file(s3_key)
        
        if downloaded_content == test_content:
            print("✅ File download and verification successful")
        else:
            print("❌ Downloaded content doesn't match uploaded content")
            return False
        
        # Test file info
        file_info = await document_service.file_service.get_file_info(s3_key)
        print(f"✅ File info: Size={file_info['size']} bytes, Type={file_info['content_type']}")
        
        # Test presigned URL generation
        presigned_url = await document_service.file_service.get_presigned_url(s3_key)
        print(f"✅ Presigned URL generated: {presigned_url[:100]}...")
        
        # Clean up
        await document_service.file_service.delete_file(s3_key)
        print("✅ Test file cleaned up")
        
        print("\n🎉 All S3 upload tests passed!")
        print("Your Supabase S3 bucket is properly configured for document storage.")
        print("File uploads will work when users are properly authenticated.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_direct_upload())
    if result:
        print("\n✅ SUMMARY: S3 file upload system is working correctly!")
        print("Next steps:")
        print("1. Set up user authentication in Supabase")
        print("2. Test with real user login")
        print("3. Upload documents through the API")
    else:
        print("\n❌ SUMMARY: S3 integration needs fixes")