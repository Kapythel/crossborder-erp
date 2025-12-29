from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/crossborder_erp"
    
    # Server
    port: int = 8000
    environment: str = "development"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    
    # Tax Rates
    texas_sales_tax_rate: float = 0.0825
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 10485760  # 10MB
    
    # Cloudinary (Optional)
    cloudinary_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
