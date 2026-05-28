#!/bin/bash
echo "=== Job Agent — Local Quick Start ==="

echo "1. Checking .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "   Created .env from .env.example — please add your Gemini API keys"
fi

echo "2. Starting with Docker Compose..."
docker compose down
docker compose up --build -d

echo ""
echo "=== Services starting ==="
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Frontend:     http://localhost:3000"
echo ""
echo "Watch logs:   docker compose logs -f"
echo "Stop:         docker compose down"
