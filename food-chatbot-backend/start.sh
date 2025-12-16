#!/bin/bash

# Quick start script for Food Chatbot Backend

echo "=================================="
echo "Food Chatbot Backend - Quick Start"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
if [ ! -f ".installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch .installed
else
    echo "Dependencies already installed."
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Check if database exists
if [ ! -f "database/chatbot.db" ]; then
    echo ""
    echo "Database not found. Running initialization..."
    echo "This will take 5-10 minutes..."
    python init_system.py
else
    echo "Database already initialized."
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo ""
    echo "WARNING: Ollama is not running!"
    echo "Please start Ollama with: ollama serve"
    echo "And pull the model: ollama pull llama3.1:8b"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Start server
echo ""
echo "Starting server..."
echo "API will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
python main.py
