# Cross-Border ERP System 🌎

A comprehensive SaaS ERP solution designed for cross-border operations between Texas and México, featuring automated OCR receipt processing, multi-tenant architecture, and Railway deployment.

## 🚀 Features

- **OCR Document Processing**: Automated receipt and customs document processing using Tesseract
- **Multi-Currency Support**: Handles both USD and MXN with automatic detection
- **Texas Sales Tax**: Automatic 8.25% sales tax calculation
- **Multi-Tenant Architecture**: Support for multiple companies with EIN and RFC tracking
- **Bank Reconciliation**: Automatic matching of OCR expenses with bank transactions
- **Customs Tracking**: Pedimento and Bill of Lading management
- **Modern UI**: Beautiful dashboard with glassmorphism effects and Tailwind CSS
- **Docker Ready**: Complete containerization for easy deployment
- **Railway Compatible**: One-click deployment to Railway platform

## 📋 Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **OCR**: Tesseract with pytesseract
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
- **Containerization**: Docker & Docker Compose
- **Deployment**: Railway

## 🛠️ Local Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Tesseract OCR
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
cd crossborder-erp

# Copy environment variables
copy .env.example .env

# Start services
docker-compose up -d

# Access the application
# Frontend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Manual Setup

```bash
# Install Tesseract OCR
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
# Mac: brew install tesseract

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env
# Edit .env with your database credentials

# Create uploads directory
mkdir uploads

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload

# Access at http://localhost:8000
```

## 🌐 Railway Deployment

### Step 1: Prepare Your Repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect the Dockerfile

### Step 3: Add PostgreSQL Database

1. In your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will automatically set `DATABASE_URL` environment variable

### Step 4: Configure Environment Variables

Add these variables in Railway dashboard under "Variables":

```
ENVIRONMENT=production
SECRET_KEY=<generate-a-secure-random-key>
TEXAS_SALES_TAX_RATE=0.0825
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760
```

Optional (for Cloudinary image storage):
```
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### Step 5: Deploy

Railway will automatically deploy. Access your app at the provided URL.

## 📸 Using the OCR Feature

1. **Upload Receipt**:
   - Navigate to "Expenses OCR" page
   - Drag and drop an image or PDF receipt
   - System will automatically detect currency (USD/MXN)

2. **Review Extracted Data**:
   - OCR extracts: vendor, date, total, tax, tip
   - Confidence level shown (High/Medium/Low)
   - **Always review and edit** extracted data

3. **Save Expense**:
   - Edit any incorrect fields
   - Add category and description
   - Click "Save Expense"

## 🔧 API Documentation

Access interactive API documentation at `/api/docs` when the server is running.

### Key Endpoints

- `POST /api/companies/` - Create company
- `POST /api/invoices/` - Create invoice (auto-calculates tax)
- `POST /api/expenses/upload` - Upload receipt for OCR
- `POST /api/expenses/` - Save expense
- `GET /api/reconciliation/` - Get bank reconciliation
- `POST /api/customs/` - Create customs log

## 🏗️ Project Structure

```
crossborder-erp/
├── app/
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic (OCR, file handling)
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # DB connection
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── frontend/
│   ├── index.html        # Dashboard
│   ├── expenses.html     # OCR upload page
│   ├── reconciliation.html
│   ├── styles/           # CSS
│   └── js/               # JavaScript
├── alembic/              # Database migrations
├── uploads/              # Receipt storage
├── Dockerfile
├── docker-compose.yml
├── railway.json
└── requirements.txt
```

## ⚠️ Important Notes

### OCR Accuracy

- **High-quality images**: 85-95% accuracy
- **Poor quality/wrinkled receipts**: May require manual editing
- **Always verify** extracted amounts and vendor names
- System is designed to allow easy corrections

### Security

- Never commit `.env` file
- Use strong `SECRET_KEY` in production
- Configure proper CORS origins in production
- Limit file upload sizes

### Database

- Automatic migrations with Alembic
- Multi-tenant design with company isolation
- Relationships enforce referential integrity

## 🧪 Testing

```bash
# Run a test OCR upload
curl -X POST http://localhost:8000/api/expenses/upload \
  -F "file=@sample_receipt.jpg" \
  -F "company_id=1"
```

## 📝 Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `PORT` | Server port | 8000 |
| `ENVIRONMENT` | dev/production | development |
| `SECRET_KEY` | Security key | Required |
| `TEXAS_SALES_TAX_RATE` | Tax rate decimal | 0.0825 |
| `UPLOAD_DIR` | File upload directory | ./uploads |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | 10485760 |
| `CLOUDINARY_URL` | Optional cloud storage | None |

## 🤝 Support

For issues or questions:
1. Check API documentation at `/api/docs`
2. Review logs in Railway dashboard
3. Verify environment variables are set correctly

## 📄 License

This project is proprietary software for cross-border operations management.

---

Built with ❤️ for Texas-México cross-border businesses
