from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from app.routers import companies, invoices, expenses, customs, reconciliation
from app.database import init_db
from app.config import settings
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cross-Border ERP System",
    description="SaaS ERP for Texas-México cross-border operations with OCR processing",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router)
app.include_router(invoices.router)
app.include_router(expenses.router)
app.include_router(customs.router)
app.include_router(reconciliation.router)

# Mount static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
uploads_path = settings.upload_dir

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

if os.path.exists(uploads_path):
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Cross-Border ERP System...")
    logger.info(f"Environment: {settings.environment}")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Cross-Border ERP System...")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main dashboard"""
    frontend_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    return HTMLResponse(content="<h1>Cross-Border ERP System</h1><p>Frontend not found. Please check installation.</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }


@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "Cross-Border ERP API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "companies": "/api/companies",
            "invoices": "/api/invoices",
            "expenses": "/api/expenses",
            "customs": "/api/customs",
            "reconciliation": "/api/reconciliation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.port))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.environment == "development"
    )
