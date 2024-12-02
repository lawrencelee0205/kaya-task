#! /bin/bash
echo "Freezeing requirements..."
pipenv requirements --dev > requirements.txt

echo "Starting docker compose services..."
docker compose up -d --build
