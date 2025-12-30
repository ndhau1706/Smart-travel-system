#!/bin/bash

# ============================================
# Food Chatbot Backend - Auto Start Script
# Cross-platform support: Linux, macOS, Windows (Git Bash/WSL)
# ============================================

set -e  # Exit on error

echo "🍜 Food Chatbot Backend - Auto Start"
echo "===================================="
echo ""

# Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
fi

echo "🖥️  Detected OS: $OS_TYPE"
echo ""

# Check Python
echo "🔍 Checking Python..."
PYTHON_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python not found!"
    echo "📥 Please install Python 3.9+ from:"
    echo "   - Linux/macOS: sudo apt install python3 (or brew install python3)"
    echo "   - Windows: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Check pip
echo "🔍 Checking pip..."
PIP_CMD=""

if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "❌ Error: pip not found!"
    echo "📥 Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade
    PIP_CMD="pip3"
fi

echo "✅ Found pip"
echo ""

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OS_TYPE" == "windows" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi
echo "✅ Virtual environment activated"
echo ""

# Get script directory to locate requirements.txt
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to script directory
cd "$SCRIPT_DIR"

# Install dependencies
echo "📦 Installing dependencies..."
echo "   This may take a few minutes on first run..."
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q
echo "✅ Dependencies installed"
echo ""

# Check .env file (skip creation, user should have it with encryption config)
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "⚠️  You need to create .env file with:"
    echo "   - GIST_URL_KEY=<your key>"
    echo "   - ENCRYPTED_GIST_URL=<your encrypted URL>"
    echo ""
    echo "📖 See GIST_UPLOAD_GUIDE.md for instructions"
    exit 1
fi

# Initialize database and indexes
echo "🗄️  Initializing database and search indexes..."
cd "$SCRIPT_DIR"
if [ ! -f "data/chatbot.db" ] || [ ! -f "data/bm25_index.pkl" ]; then
    echo "   Building indexes for the first time (this takes 30-60 seconds)..."
    $PYTHON_CMD -c "
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

async def init():
    from database.db_manager import db_manager
    await db_manager.init_db()
    print('✅ Database initialized')
    
    from services.vector_store import vector_store
    from services.bm25_search import bm25_search
    
    if not vector_store.load_index():
        print('⚠️  FAISS index not found, building from scratch...')
        vector_store.build_index()
        vector_store.save_index()
        print('✅ FAISS index built')
    else:
        print('✅ FAISS index loaded')
    
    if not bm25_search.load_index():
        print('⚠️  BM25 index not found, building from scratch...')
        bm25_search.build_index()
        bm25_search.save_index()
        print('✅ BM25 index built')
    else:
        print('✅ BM25 index loaded')

asyncio.run(init())
"
else
    echo "✅ Database and indexes already exist"
fi
echo ""

# Start server
echo "🚀 Starting Food Chatbot Backend..."
echo ""
echo "📍 Server will be available at:"
echo "   - http://localhost:8000"
echo "   - http://127.0.0.1:8000"
echo ""
echo "📚 API Documentation:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""
echo "============================================"
echo ""

# Change to script directory before running
cd "$SCRIPT_DIR"

# Run the server
$PYTHON_CMD main.py
