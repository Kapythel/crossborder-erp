# Railway Deployment Guide 🚂

Step-by-step guide to deploy the Cross-Border ERP System to Railway.

## Prerequisites

- GitHub account
- Railway account ([railway.app](https://railway.app))
- Git installed locally

## Step 1: Prepare Your Code

### 1.1 Initialize Git Repository (if not already done)

```bash
cd C:\Users\LENOVO\.gemini\antigravity\scratch\crossborder-erp

git init
git add .
git commit -m "Initial commit: Cross-Border ERP System"
```

### 1.2 Create GitHub Repository

1. Go to GitHub.com
2. Click "New Repository"
3. Name it `crossborder-erp`
4. Don't initialize with README (we already have one)
5. Click "Create repository"

### 1.3 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/crossborder-erp.git
git branch -M main
git push -u origin main
```

## Step 2: Create Railway Project

### 2.1 Sign Up/Login to Railway

1. Go to [railway.app](https://railway.app)
2. Click "Login" and connect your GitHub account
3. Authorize Railway to access your repositories

### 2.2 Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `crossborder-erp` repository
4. Railway will automatically detect the `Dockerfile`

### 2.3 Initial Deployment

- Railway will start building your Docker image
- This may take 3-5 minutes on first deployment
- Don't worry if it fails initially - we need to add the database first

## Step 3: Add PostgreSQL Database

### 3.1 Add Database Service

1. In your Railway project dashboard, click "+ New"
2. Select "Database"
3. Choose "Add PostgreSQL"
4. Railway will provision a PostgreSQL database

### 3.2 Automatic Configuration

Railway automatically creates a `DATABASE_URL` environment variable that links your app to the database. No manual configuration needed!

## Step 4: Configure Environment Variables

### 4.1 Access Variables Tab

1. Click on your web service (not the database)
2. Go to "Variables" tab

### 4.2 Add Required Variables

Click "+ New Variable" for each of these:

```
ENVIRONMENT=production
SECRET_KEY=<generate-a-strong-random-key-here>
TEXAS_SALES_TAX_RATE=0.0825
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760
```

#### How to Generate SECRET_KEY:

**Option 1 - Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 2 - Online:**
Use [randomkeygen.com](https://randomkeygen.com/) - Choose "CodeIgniter Encryption Keys"

### 4.3 Optional: Add Cloudinary (for production image storage)

If you want to use Cloudinary for image storage instead of local storage:

1. Create account at [cloudinary.com](https://cloudinary.com)
2. Copy your "API Environment variable" from dashboard
3. Add to Railway:
```
CLOUDINARY_URL=cloudinary://123456789012345:abcdefghijklmnopqrstuvwxyz@your-cloud-name
```

## Step 5: Deploy and Verify

### 5.1 Trigger Deployment

After adding environment variables, Railway will automatically redeploy. If not:

1. Go to "Deployments" tab
2. Click "Deploy" on the latest commit

### 5.2 Check Build Logs

1. Click on the active deployment
2. Watch the build logs
3. Look for:
   - "Installing tesseract-ocr" ✓
   - "Installing Python dependencies" ✓
   - "Starting server" ✓

### 5.3 Get Your App URL

1. Go to "Settings" tab
2. Scroll to "Domains"
3. Click "Generate Domain"
4. Your app will be available at: `https://your-app-name.up.railway.app`

## Step 6: Initialize Database

### 6.1 Run Migrations (Optional)

If using Alembic migrations:

1. Go to your web service
2. Click on "Settings" → "Deploy Triggers"  
3. Add a "Command" deploy:
```bash
alembic upgrade head
```

Alternatively, the app will auto-create tables on first startup.

### 6.2 Create First Company

1. Open your Railway app URL
2. Click "+ Add Company"
3. Fill in:
   - Name: Your company name
   - EIN: Tax ID (e.g., `12-3456789`)
   - Texas Sales Tax ID: (optional)
   - RFC: México tax ID (optional)
4. Click "Add Company"

## Step 7: Test OCR Functionality

### 7.1 Upload Test Receipt

1. Navigate to "Expenses OCR" page
2. Drag and drop a receipt image (JPG, PNG, or PDF)
3. Wait for OCR processing (5-15 seconds)
4. Review extracted data

### 7.2 Verify Results

- Check if currency was detected correctly (USD/MXN)
- Verify amounts extracted
- Edit any incorrect fields
- Save expense

## Troubleshooting

### Build Failed

**Error: "Tesseract not found"**
- Check Dockerfile includes `tesseract-ocr` installation
- Rebuild deployment

**Error: "Port not found"**
- Ensure `uvicorn` command uses `--port $PORT`
- Railway sets PORT automatically

### Runtime Errors

**500 Internal Server Error on `/api/expenses/upload`**
- Check Railway logs: Click service → "View Logs"
- Verify Tesseract is installed: Look for installation in build logs
- Check file size limits

**Database Connection Failed**
- Verify PostgreSQL database is running
- Check `DATABASE_URL` variable exists
- Restart web service

### OCR Not Working

**Low accuracy or errors**
- Ensure image quality is good
- Try different image formats (PNG usually works best)
- Remember: OCR is designed to be edited manually

**Upload fails**
- Check file size (default max: 10MB)
- Verify file format (JPG, PNG, PDF only)
- Check Railway logs for specific error

## Monitoring & Maintenance

### View Logs

```
Railway Dashboard → Your Service → View Logs
```

### Check Resource Usage

```
Railway Dashboard → Your Service → Metrics
```

### Update Deployment

```bash
# Make changes locally
git add .
git commit -m "Update: description of changes"
git push

# Railway auto-deploys on push
```

### Scale (if needed)

1. Go to "Settings" → "Scaling"
2. Adjust replicas or resources
3. Note: Free tier has limitations

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✓ | Auto-set by Railway | postgres://... |
| `PORT` | ✓ | Auto-set by Railway | 8000 |
| `ENVIRONMENT` | ✓ | App environment | production |
| `SECRET_KEY` | ✓ | Security key | random-string-here |
| `TEXAS_SALES_TAX_RATE` | ✓ | Tax rate | 0.0825 |
| `UPLOAD_DIR` | ✓ | Upload directory | ./uploads |
| `MAX_UPLOAD_SIZE` | ✓ | Max file size (bytes) | 10485760 |
| `CLOUDINARY_URL` | - | Cloud storage | cloudinary://... |

## Security Checklist

- [x] Strong SECRET_KEY generated
- [x] ENVIRONMENT set to "production"
- [ ] CORS origins configured (if needed)
- [ ] File upload limits set
- [ ] Database backups enabled (Railway Pro)

## Next Steps

1. ✅ App deployed and running
2. ✅ Company created
3. ✅ OCR tested
4. 📱 Share app URL with team
5. 📊 Monitor usage and performance
6. 🔐 Set up user authentication (future enhancement)

## Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Project Logs: Railway Dashboard → View Logs

---

🎉 Your Cross-Border ERP is now live on Railway!
