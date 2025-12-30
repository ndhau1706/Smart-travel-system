# Smart Travel System

A modern restaurant booking and food discovery platform built with React, TypeScript, and FastAPI.

## Features

- **Restaurant Discovery**: Browse and search restaurants with filters
- **Online Booking**: Book tables with real-time availability
- **Reviews & Ratings**: Read and write restaurant reviews
- **AI Chatbot**: Get personalized food recommendations
- **User Authentication**: Secure login with OTP verification
- **Responsive Design**: Works on desktop and mobile

## Architecture

```
Smart-Travel-System/
├── New_Frontend/           # Frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── stores/         # Zustand state stores
│   │   ├── hooks/          # Custom React hooks
│   │   └── lib/            # Utilities and configs
│   └── backend/            # Backend API
│       ├── app/
│       │   ├── core/       # Core services (auth, db, etc.)
│       │   ├── modules/    # Feature modules
│       │   └── shared/     # Shared utilities
│       └── tests/          # Test files
└── plans/                  # Architecture documentation
```

## Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Radix UI / shadcn/ui** - Component library
- **React Query** - Data fetching & caching
- **Zustand** - State management
- **React Router** - Routing

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL / SQLite** - Database
- **JWT** - Authentication
- **Pydantic** - Data validation

### Infrastructure
- **Google Cloud Run** - Container hosting
- **Cloud SQL** - Managed PostgreSQL
- **Cloud Storage** - Image storage

## Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- pnpm or npm

### Frontend Setup

```bash
cd New_Frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Backend Setup

```bash
cd New_Frontend/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py
```

## Configuration

### Frontend Environment Variables

Copy `New_Frontend/.env.example` to `New_Frontend/.env` and fill values:

```env
# Can be backend root or backend /api prefix (both supported)
VITE_API_BASE_URL=http://localhost:8000
# VITE_API_BASE_URL=http://localhost:8000/api

# Firebase Authentication (optional)
# If these are not set, the app will fall back to the legacy OTP/JWT auth flow.
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_APP_ID=
```

### Backend Environment Variables

Copy `New_Frontend/backend/.env.example` to `New_Frontend/backend/.env` and fill values:

```env
# Application
APP_NAME=Smart Travel System API
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./smart_travel.db
# For production:
# CLOUD_SQL_CONNECTION_NAME=project:region:instance
# DB_USER=appuser
# DB_PASS=password
# DB_NAME=smarttravel

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Brevo (for OTP)
BREVO_API_KEY=
EMAIL_FROM=no-reply@example.com
EMAIL_FROM_NAME=Smart Travel
# Optional SMTP fallback (Brevo)
BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_USER=
BREVO_SMTP_PASSWORD=
# OTP settings
OTP_TTL_MIN=10
OTP_MAX_ATTEMPTS=5
OTP_RESEND_LIMIT_PER_HOUR=5

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Firebase Authentication (backend token verification)
# If your Firebase Project ID differs from GOOGLE_CLOUD_PROJECT, set it here.
FIREBASE_PROJECT_ID=
```

## Firebase Authentication (Optional)

This project supports a hybrid auth setup:

- If `VITE_FIREBASE_*` is configured, the UI uses Firebase Auth (Email/Password + Google) and exchanges the Firebase ID token with the backend via `POST /auth/firebase` to get the app's JWT tokens.
- If `VITE_FIREBASE_*` is missing, the UI falls back to the legacy OTP/JWT auth flow.

### Setup steps

1. Create a Firebase project in Firebase Console.
2. Enable providers in **Authentication → Sign-in method**:
   - Email/Password
   - Google (recommended)
3. Add a **Web App** and copy the config values into `New_Frontend/.env` (`VITE_FIREBASE_*`).
4. Backend verifies Firebase ID tokens using `firebase-admin` (already included in `requirements.txt`).
   - On Cloud Run it uses Application Default Credentials.
   - If your Firebase Project ID differs from `GOOGLE_CLOUD_PROJECT`, set `FIREBASE_PROJECT_ID` on the backend service.

## Testing

### Backend Tests

```bash
cd New_Frontend/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py -v
```

### Frontend Tests

```bash
cd New_Frontend

# Run tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Guide**: [backend/docs/API.md](New_Frontend/backend/docs/API.md)

## Security Features

- JWT authentication with access/refresh tokens
- OTP-based email verification
- Password hashing with bcrypt
- Rate limiting (100 req/min, 2000 req/hour)
- Admin-only endpoints protection
- CORS configuration
- Input validation with Pydantic

## Project Structure

### Frontend Components

```
src/
├── components/
│   ├── ui/              # shadcn/ui components
│   ├── AuthDialog.tsx   # Login/Register dialog
│   ├── BookingDialog.tsx
│   ├── Navigation.tsx
│   ├── UserMenu.tsx
│   └── ErrorBoundary.tsx
├── pages/
│   ├── Home/
│   ├── Restaurants/
│   ├── Bookings/
│   ├── Chatbot/
│   ├── Reviews/
│   └── ...
├── stores/
│   ├── authStore.ts     # Authentication state
│   └── uiStore.ts       # UI state (theme, modals)
├── hooks/
│   ├── useRestaurants.ts
│   ├── useAuth.ts
│   └── useBookings.ts
└── services/
    ├── api.ts           # Restaurant API
    └── auth.ts          # Auth API
```

### Backend Modules

```
app/
├── core/
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   ├── security.py      # JWT utilities
│   ├── admin_auth.py    # Admin authentication
│   ├── exceptions.py    # Error handling
│   ├── logging_config.py
│   ├── rate_limit.py
│   └── cache.py
├── modules/
│   ├── auth/            # Authentication
│   ├── users/           # User management
│   ├── restaurants/     # Restaurant CRUD
│   ├── bookings/        # Booking management
│   ├── reviews/         # Review system
│   ├── chat/            # Chatbot
│   └── contact/         # Contact form
└── shared/
    ├── schemas.py       # Base response schemas
    └── email_service.py
```

## Deployment

### Docker Build

```bash
# Frontend
cd New_Frontend
docker build -t smart-travel-frontend .

# Backend
cd New_Frontend/backend
docker build -t smart-travel-backend .
```

### Google Cloud Run

```bash
# Deploy backend
gcloud run deploy smart-travel-backend \
  --image gcr.io/PROJECT_ID/smart-travel-backend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated

# Deploy frontend
gcloud run deploy smart-travel-frontend \
  --image gcr.io/PROJECT_ID/smart-travel-frontend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

### CI/CD on Google Cloud (Cloud Build → Cloud Run)

Use the provided `cloudbuild.yaml` to build/push both backend & frontend images, then deploy them to Cloud Run automatically.

1) Enable APIs (one-time):
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com
```
2) Create an Artifact Registry repo (one-time):
```bash
gcloud artifacts repositories create smart-travel --repository-format=docker --location=asia-southeast1
```
3) Connect GitHub: Cloud Build → Triggers → “Manage repositories” → GitHub → pick `nhathuybs/TDTT`.
4) Create a trigger:
   - Source: branch `main` (or your target branch)
   - Config: `cloudbuild.yaml`
   - Substitutions to set:
     - `_REGION` (e.g. `asia-southeast1`)
     - `_REPOSITORY` (artifact registry repo name, e.g. `smart-travel`)
     - `_BACKEND_SERVICE`, `_FRONTEND_SERVICE` (Cloud Run service names)
     - Database (choose one):
       - Provide full `_DATABASE_URL` (e.g. `postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance`)
       - Or set `_DB_USER`, `_DB_PASS`, `_DB_NAME`, `_DB_TYPE` (`postgres`/`mysql`) plus `_CLOUD_SQL_CONNECTION` to auto-build the URL
     - Optional: `_API_BASE_URL` (defaults to backend service URL + `/api`), `_SECRET_KEY`
5) Deploy env/secrets:
   - Backend Cloud Run: set envs for `DATABASE_URL`/`CLOUD_SQL_CONNECTION_NAME`, `SECRET_KEY`, email configs, `CORS_ORIGINS`.
   - Frontend Cloud Run: `VITE_API_BASE_URL` can be `<backend-url>` or `<backend-url>/api` (pipeline default is backend URL + `/api`).
6) Verify: after trigger runs, check Cloud Run services for URLs; frontend should call the backend URL over HTTPS.

Notes:
- Cloud SQL: supply `_CLOUD_SQL_CONNECTION` (format `project:region:instance`) and `DATABASE_URL` using the `/cloudsql/` host socket for asyncpg.
- Artifacts are pushed to `${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/backend:latest` and `/frontend:latest`.

## Performance

- **Frontend**: Vite for fast HMR, React Query for caching
- **Backend**: Async SQLAlchemy, in-memory caching
- **Database**: Connection pooling, indexed queries

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **Smart Travel Team** - *Initial work*

## Acknowledgments

- [shadcn/ui](https://ui.shadcn.com/) for the beautiful components
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing framework
- [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS
