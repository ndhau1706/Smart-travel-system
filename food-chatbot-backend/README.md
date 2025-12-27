# 🍽️ Food Chatbot Backend - TP.HCM Restaurant Recommendation

AI-powered chatbot backend for restaurant recommendations in Ho Chi Minh City, Vietnam.

[![CI/CD](https://github.com/your-repo/food-chatbot-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/your-repo/food-chatbot-backend/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Docker Deployment](#-docker-deployment)
- [Frontend Integration](#-frontend-integration)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI-Powered** | Groq Cloud LLM (Llama 3.3 70B) with fallback |
| 🔍 **Hybrid Search** | FAISS vector + BM25 keyword search |
| 💬 **Multi-turn Chat** | Context-aware conversation sessions |
| 🔐 **JWT Auth** | Secure authentication with token refresh |
| 📊 **Monitoring** | Prometheus metrics + Sentry error tracking |
| 🐳 **Docker Ready** | One-command deployment |
| ⚡ **High Performance** | Async/await, Redis caching |
| 🛡️ **Security** | Rate limiting, CSRF, input validation |

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (Python 3.13 recommended)
- **pip** (Python package manager)
- **Groq API Key** (get free at [console.groq.com](https://console.groq.com/keys))

### Option 1: Auto Start (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd food-chatbot-backend

# Run auto start script
chmod +x autoStart.sh
./autoStart.sh
```

The script will automatically:
1. Detect your OS (Linux/macOS/Windows)
2. Check Python installation
3. Create virtual environment
4. Install dependencies
5. Initialize database and search indexes
6. Start the server at http://localhost:8000

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone <your-repo-url>
cd food-chatbot-backend

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure .env
cp .env.example .env
nano .env  # Edit and add your Groq API key

# 5. Initialize database and indexes
python -c "
import asyncio
from database.db_manager import db_manager
from services.vector_store import vector_store
from services.bm25_search import bm25_search

async def init():
    await db_manager.init_db()
    vector_store.build_index()
    vector_store.save_index()
    bm25_search.build_index()
    bm25_search.save_index()

asyncio.run(init())
"

# 6. Start server
python main.py
```

## 🔑 API Key Setup

1. **Get Groq API Key**:
   - Go to [console.groq.com/keys](https://console.groq.com/keys)
   - Sign up (free)
   - Create new API key
   - Copy the key (starts with `gsk_...`)

2. **Add to .env**:
   ```bash
   nano .env
   ```
   
   Replace `your_groq_api_key_here` with your actual key:
   ```env
   GROQ_API_KEYS=gsk_your_actual_key_here
   ```

3. **Multiple Keys** (for higher rate limits):
   ```env
   GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3
   ```

See [APIKey.md](../APIKey.md) for detailed instructions.

## 📡 API Endpoints

### Health Check
```bash
GET /
```

### Chat
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Tìm quán phở ngon gần Quận 1",
  "session_id": "optional-session-id"
}
```

### Sessions
```bash
# Get all sessions
GET /api/sessions

# Get session messages
GET /api/sessions/{session_id}/messages

# Delete session
DELETE /api/sessions/{session_id}
```

### Feedback
```bash
POST /api/feedback
Content-Type: application/json

{
  "message_id": "msg_123",
  "rating": 5,
  "comment": "Great recommendation!"
}
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗂️ Project Structure

```
food-chatbot-backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── autoStart.sh           # Auto setup and start script
├── .env                   # Environment variables (create from .env.example)
│
├── config/                # Configuration
│   ├── settings.py        # App settings (from .env)
│   └── synonyms.py        # Vietnamese food synonyms
│
├── database/              # Database layer
│   ├── db_manager.py      # SQLite async manager
│   └── redis_manager.py   # Redis cache (optional)
│
├── middleware/            # FastAPI middleware
│   ├── csrf_protection.py # CSRF token validation
│   └── rate_limiter.py    # Rate limiting
│
├── models/                # Pydantic models
│   └── schemas.py         # Request/response schemas
│
├── routes/                # API routes
│   ├── chat.py            # Chat endpoints
│   ├── sessions.py        # Session management
│   └── feedback.py        # User feedback
│
├── services/              # Business logic
│   ├── groq_service.py    # Groq LLM integration
│   ├── vector_store.py    # FAISS vector search
│   ├── bm25_search.py     # BM25 keyword search
│   ├── hybrid_search.py   # Hybrid search (FAISS + BM25)
│   ├── rag_pipeline.py    # RAG (Retrieval Augmented Generation)
│   ├── context_tracker.py # Multi-turn context
│   └── ...                # Other services
│
└── utils/                 # Utilities
    ├── key_manager.py     # API key encryption
    ├── response_formatter.py  # Format chat responses
    ├── advanced_parser.py # Parse user queries
    └── ...                # Other utilities
```

## 🛠️ Development

### Run in Debug Mode

```bash
# In .env, set:
DEBUG=True

# Start server
python main.py
```

### Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Integration tests
pytest tests/integration/ -v

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type checking
mypy .
```

## 🔒 Security Features

- **CSRF Protection**: Token-based CSRF validation
- **Rate Limiting**: 
  - 30 requests/minute per user
  - 1800 requests/hour
  - 14400 requests/day
- **API Key Encryption**: Fernet encryption for secure API key storage
- **Password Hashing**: Bcrypt with 12 rounds
- **Input Validation**: Pydantic models with strict validation

## 🌐 Deployment

### Option 1: Local Development
```bash
./autoStart.sh
```

### Option 2: Docker (Recommended for Production)
```bash
# Quick start with Docker Compose
docker-compose up -d

# With monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### Option 3: Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Production Deployment Guide

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Docker deployment
- SSL/TLS setup with Let's Encrypt
- Nginx configuration
- Kubernetes deployment
- Scaling and load balancing

### PostgreSQL Migration

For high-traffic production environments, see [docs/POSTGRESQL_MIGRATION.md](docs/POSTGRESQL_MIGRATION.md)

## 🎨 Frontend Integration

### Quick Start for Frontend Developers

1. **Clone and start backend:**
```bash
git clone <repo-url>
cd food-chatbot-backend
./autoStart.sh
```

2. **Test API is running:**
```bash
curl http://localhost:8000/health
```

3. **Read API documentation:**
- Swagger UI: http://localhost:8000/docs
- Full guide: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Example React Integration

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

// Login
const { data } = await api.post('/auth/login', {
  username: 'testuser',
  password: 'password123'
});
const token = data.access_token;

// Chat (authenticated)
const response = await api.post('/api/chat', 
  { message: 'Tìm quán phở ngon' },
  { headers: { Authorization: `Bearer ${token}` }}
);
console.log(response.data.restaurants);
```

### CORS Configuration

Frontend origins already configured for development:
- `http://localhost:3000` (React)
- `http://localhost:5173` (Vite)

For production, update `.env.production`:
```env
CORS_ORIGINS=https://your-frontend.com
```

## 📝 Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `GROQ_API_KEYS` | Groq API keys (comma-separated) | Required |
| `GROQ_MODEL` | Primary LLM model | `llama-3.3-70b-versatile` |
| `RPM_LIMIT` | Requests per minute limit | `30` |
| `REDIS_ENABLED` | Enable Redis caching | `False` |
| `DEBUG` | Debug mode | `False` |

See `.env.example` for full list.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/food-chatbot-backend.git

# 2. Create feature branch
git checkout -b feature/your-feature

# 3. Setup and start
./autoStart.sh

# 4. Make changes and test
pytest tests/

# 5. Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature

# 6. Create Pull Request on GitHub
```

### Commit Convention

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Add tests
- `refactor:` Code refactoring

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Full API reference for frontend |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [docs/POSTGRESQL_MIGRATION.md](docs/POSTGRESQL_MIGRATION.md) | Database migration guide |
| [TODO.md](TODO.md) | Development progress tracking |

## 📄 License

MIT License - feel free to use for learning purposes.

## 🆘 Troubleshooting

### Python not found
```bash
# Linux/macOS
sudo apt install python3  # Debian/Ubuntu
brew install python3      # macOS

# Windows
# Download from python.org
```

### Module not found
```bash
# Activate virtual environment first
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### API key error
```bash
# Check .env file has correct key
cat .env | grep GROQ_API_KEYS

# Should see: GROQ_API_KEYS=gsk_...
# NOT: GROQ_API_KEYS=your_groq_api_key_here
```

### Port 8000 already in use
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process or change PORT in .env
```

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Team Chat**: Contact via team communication channel
- **Documentation**: See APIKey.md for API key setup

---

**Built with ❤️ for TP.HCM food lovers**
