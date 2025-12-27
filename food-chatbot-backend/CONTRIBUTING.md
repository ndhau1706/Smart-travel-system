# Contributing to Food Chatbot Backend

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Style Guide](#style-guide)
8. [Architecture Overview](#architecture-overview)

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for full stack testing)
- VS Code (recommended) with Python extension

### Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/food-chatbot-backend.git
cd food-chatbot-backend

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/food-chatbot-backend.git
```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

# Install development dependencies
pip install black isort ruff mypy pytest-cov
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Groq API key
```

### 4. Start Development Server

```bash
uvicorn main:app --reload --port 8000
```

### 5. Verify Setup

```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

---

## Making Changes

### 1. Create a Branch

```bash
# Sync with upstream first
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Branch Naming Convention

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/add-restaurant-images` |
| Bug Fix | `fix/description` | `fix/session-timeout` |
| Docs | `docs/description` | `docs/api-examples` |
| Refactor | `refactor/description` | `refactor/auth-service` |
| Test | `test/description` | `test/feedback-api` |

### 3. Make Your Changes

- Keep commits small and focused
- Write clear commit messages
- Add tests for new features
- Update documentation if needed

### 4. Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

# Types:
feat: New feature
fix: Bug fix
docs: Documentation only
style: Formatting, no code change
refactor: Code change, no new feature or fix
test: Adding tests
chore: Maintenance tasks

# Examples:
git commit -m "feat(auth): add password reset endpoint"
git commit -m "fix(chat): handle empty message gracefully"
git commit -m "docs(api): add streaming examples"
git commit -m "test(sessions): add integration tests"
```

---

## Testing

### Run All Tests

```bash
# Quick test
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html --cov-fail-under=60
open htmlcov/index.html  # View coverage report
```

### Run Specific Tests

```bash
# Single file
pytest tests/unit/test_auth.py -v

# Single test
pytest tests/unit/test_auth.py::test_login_success -v

# By marker
pytest -m "not slow" -v
```

### Write Tests

```python
# tests/unit/test_your_feature.py
import pytest
from your_module import your_function

class TestYourFeature:
    """Tests for your feature."""
    
    def test_success_case(self):
        """Test normal operation."""
        result = your_function("valid_input")
        assert result is not None
        assert result.status == "success"
    
    def test_edge_case(self):
        """Test edge case handling."""
        result = your_function("")
        assert result.status == "error"
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async operation."""
        result = await your_async_function()
        assert result is True
```

### Load Testing

```bash
# Start the server first
uvicorn main:app --port 8000

# In another terminal
locust -f tests/load/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 for web UI
```

---

## Pull Request Process

### 1. Before Submitting

```bash
# Run tests
pytest tests/

# Format code
black .
isort .

# Check linting
ruff check .

# Update your branch with latest main
git fetch upstream
git rebase upstream/main
```

### 2. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- **Clear title** following commit convention
- **Description** explaining what and why
- **Link to related issues** if any
- **Screenshots** for UI changes

### 3. PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added for new code
```

### 4. Code Review

- Address all feedback
- Keep discussions focused
- Request re-review after changes
- Be patient - reviewers are volunteers

---

## Style Guide

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

```python
# Good
from fastapi import APIRouter, Depends, HTTPException
from models import ChatRequest, ChatResponse
from services import rag_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Process a chat message and return AI response.
    
    Args:
        request: The chat request containing the message
        current_user: The authenticated user
        
    Returns:
        ChatResponse with AI message and restaurants
        
    Raises:
        HTTPException: If processing fails
    """
    result = await rag_pipeline.process(request.message)
    return ChatResponse(**result)
```

### Formatting Tools

```bash
# Format with Black (line length 88)
black .

# Sort imports
isort .

# Lint with Ruff
ruff check . --fix
```

### Type Hints

Always use type hints:

```python
# Good
def get_restaurant(id: str) -> Restaurant | None:
    ...

async def search(query: str, limit: int = 10) -> list[Restaurant]:
    ...

# Avoid
def get_restaurant(id):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> dict:
    """
    Brief description of what the function does.
    
    Longer description if needed, explaining the algorithm,
    important notes, or usage examples.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'status': 'success'}
    """
    ...
```

---

## Architecture Overview

### Project Structure

```
food-chatbot-backend/
├── main.py              # FastAPI app entry point
├── config/              # Configuration and settings
├── database/            # Database managers (SQLite, Redis)
├── middleware/          # Auth, rate limiting, CSRF
├── models/              # Pydantic schemas
├── routes/              # API endpoints
├── services/            # Business logic
├── tests/               # Test suites
└── utils/               # Helper functions
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| RAG Pipeline | Core AI processing | `services/rag_pipeline.py` |
| Hybrid Search | FAISS + BM25 search | `services/hybrid_search.py` |
| Auth Service | JWT authentication | `services/auth_service.py` |
| Session Manager | Conversation history | `services/session_manager.py` |

### Data Flow

```
User Request → Middleware (Auth, Rate Limit)
            → Route Handler
            → Service Layer (Business Logic)
            → Database/External APIs
            → Response Formatting
            → JSON Response
```

### Adding New Features

1. **New Endpoint**:
   - Add route in `routes/`
   - Add schemas in `models/schemas.py`
   - Add service logic in `services/`
   - Add tests in `tests/`

2. **New Service**:
   - Create service in `services/`
   - Export in `services/__init__.py`
   - Add tests

3. **New Middleware**:
   - Create in `middleware/`
   - Register in `main.py`

---

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email directly (don't open public issue)

---

## Recognition

Contributors will be added to the README. Thank you for helping improve this project!

---

*Happy coding! 🚀*
