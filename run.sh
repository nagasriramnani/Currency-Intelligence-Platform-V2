#!/bin/bash

# Currency Intelligence Platform - Startup Script
# This script starts both backend and frontend services

set -e

echo "🚀 Starting Currency Intelligence Platform..."
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Backend setup
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install -q -r requirements.txt

echo "✅ Backend ready"
echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --silent
fi

echo "✅ Frontend ready"
echo ""

# Start services
echo "🎬 Starting services..."
echo ""

# Start backend in background
cd ../backend
source venv/bin/activate
echo "🔧 Starting backend API on http://localhost:8000"
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start frontend
cd ../frontend
echo "🎨 Starting frontend dashboard on http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ Currency Intelligence Platform is running!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Shutdown complete"
    exit 0
}

# Register cleanup on script exit
trap cleanup INT TERM

# Wait for processes
wait


