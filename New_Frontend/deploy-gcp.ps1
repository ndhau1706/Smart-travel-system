# ============================================
# SMART TRAVEL SYSTEM - Google Cloud Deploy Script (Windows)
# ============================================

# Configuration
$PROJECT_ID = "smart-travel-sys-2025"
$REGION = "asia-southeast1"             # Singapore (gần Việt Nam)

# Service names
$BACKEND_SERVICE = "smart-travel-api"
$FRONTEND_SERVICE = "smart-travel-web"
$CHATBOT_SERVICE = "smart-travel-chatbot"
$JWT_SECRET_NAME = "jwt-secret-key"

Write-Host "🚀 Deploying Smart Travel System to Google Cloud Run" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "`n📦 Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# ============================================
# DEPLOY BACKEND
# ============================================
Write-Host "`n🔧 Building and deploying Backend..." -ForegroundColor Yellow
Set-Location backend

if ($env:FIREBASE_PROJECT_ID) {
  gcloud run deploy $BACKEND_SERVICE `
    --source . `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --update-secrets "SECRET_KEY=$($JWT_SECRET_NAME):latest" `
    --update-env-vars "FIREBASE_PROJECT_ID=$env:FIREBASE_PROJECT_ID"
} else {
  gcloud run deploy $BACKEND_SERVICE `
    --source . `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --update-secrets "SECRET_KEY=$($JWT_SECRET_NAME):latest"
}

# Get backend URL
$BACKEND_URL = gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)'
Write-Host "✅ Backend deployed at: $BACKEND_URL" -ForegroundColor Green

# ============================================
# DEPLOY CHATBOT BACKEND
# ============================================
Write-Host "`n🤖 Building and deploying Chatbot Backend..." -ForegroundColor Yellow
Set-Location ..\..\Smart-travel-system-chatbot\food-chatbot-backend

$ExistingFrontendUrl = ""
try {
  $ExistingFrontendUrl = gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)'
} catch {
  $ExistingFrontendUrl = ""
}

$AllowedOrigins = @("http://localhost:5173")
if ($ExistingFrontendUrl) { $AllowedOrigins += $ExistingFrontendUrl }
$AllowedOriginsArg = $AllowedOrigins -join ";"

gcloud run deploy $CHATBOT_SERVICE `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 6 `
  --startup-probe "httpGet.path=/health,httpGet.port=8080,initialDelaySeconds=20,timeoutSeconds=5,periodSeconds=10,failureThreshold=18" `
  --update-env-vars "ALLOWED_ORIGINS=$AllowedOriginsArg"

$CHATBOT_URL = gcloud run services describe $CHATBOT_SERVICE --region $REGION --format 'value(status.url)'
Write-Host "✅ Chatbot deployed at: $CHATBOT_URL" -ForegroundColor Green

# ============================================
# DEPLOY FRONTEND
# ============================================
Write-Host "`n🎨 Building and deploying Frontend..." -ForegroundColor Yellow
Set-Location ..\..\New_Frontend

$BuildEnv = @()
$BuildEnv += "VITE_API_BASE_URL=$BACKEND_URL/api"
$BuildEnv += "VITE_CHATBOT_API_URL=$CHATBOT_URL"
if ($env:VITE_FIREBASE_API_KEY) { $BuildEnv += "VITE_FIREBASE_API_KEY=$env:VITE_FIREBASE_API_KEY" }
if ($env:VITE_FIREBASE_AUTH_DOMAIN) { $BuildEnv += "VITE_FIREBASE_AUTH_DOMAIN=$env:VITE_FIREBASE_AUTH_DOMAIN" }
if ($env:VITE_FIREBASE_PROJECT_ID) { $BuildEnv += "VITE_FIREBASE_PROJECT_ID=$env:VITE_FIREBASE_PROJECT_ID" }
if ($env:VITE_FIREBASE_APP_ID) { $BuildEnv += "VITE_FIREBASE_APP_ID=$env:VITE_FIREBASE_APP_ID" }
if ($env:VITE_FIREBASE_MESSAGING_SENDER_ID) { $BuildEnv += "VITE_FIREBASE_MESSAGING_SENDER_ID=$env:VITE_FIREBASE_MESSAGING_SENDER_ID" }
if ($env:VITE_FIREBASE_STORAGE_BUCKET) { $BuildEnv += "VITE_FIREBASE_STORAGE_BUCKET=$env:VITE_FIREBASE_STORAGE_BUCKET" }
$BuildEnvArg = $BuildEnv -join ","

gcloud run deploy $FRONTEND_SERVICE `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --memory 256Mi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 10 `
  --set-build-env-vars "$BuildEnvArg"

# Get frontend URL
$FRONTEND_URL = gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)'

# Update chatbot CORS with the final frontend URL
if ($FRONTEND_URL) {
  $FinalOrigins = @("http://localhost:5173", $FRONTEND_URL)
  $FinalOriginsArg = $FinalOrigins -join ";"
  gcloud run services update $CHATBOT_SERVICE `
    --region $REGION `
    --update-env-vars "ALLOWED_ORIGINS=$FinalOriginsArg"
}

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host "🌐 Frontend: $FRONTEND_URL" -ForegroundColor Cyan
Write-Host "🔧 Backend API: $BACKEND_URL" -ForegroundColor Cyan
Write-Host "🤖 Chatbot API: $CHATBOT_URL" -ForegroundColor Cyan
Write-Host "📚 API Docs: $BACKEND_URL/docs" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Green
