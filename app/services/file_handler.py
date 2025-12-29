import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Service for handling file uploads"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.gif', '.bmp'}
    ALLOWED_CONTENT_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 
        'image/gif', 'image/bmp', 'application/pdf'
    }
    
    def __init__(self):
        """Initialize file handler"""
        self.upload_dir = settings.upload_dir
        self.max_size = settings.max_upload_size
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check content type
        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )
        
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File extension not allowed. Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
    
    async def save_file(self, file: UploadFile) -> Tuple[str, bytes]:
        """
        Save uploaded file and return path and bytes
        
        Returns:
            Tuple of (file_path, file_bytes)
        """
        # Validate file
        self.validate_file(file)
        
        # Read file bytes
        file_bytes = await file.read()
        
        # Check file size
        if len(file_bytes) > self.max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.max_size / 1024 / 1024}MB"
            )
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            logger.info(f"File saved: {file_path}")
            return file_path, file_bytes
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail="Error saving file")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def get_file_url(self, file_path: str) -> str:
        """Get URL for file (relative path for local storage)"""
        # For local storage, return relative path
        # In production with Cloudinary, this would return the Cloudinary URL
        return f"/uploads/{os.path.basename(file_path)}"
