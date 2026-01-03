#!/bin/bash

# Cable Ampacity Design Assistant - Startup Script

echo "Starting Cable Ampacity Design Assistant..."

# Check Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt --quiet

# Start backend in background
echo "Starting backend server on http://localhost:8000..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "==================================="
echo "Cable Ampacity Design Assistant"
echo "==================================="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "==================================="

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
