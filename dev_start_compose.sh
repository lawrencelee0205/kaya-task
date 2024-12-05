#! /bin/bash
echo "Freezing requirements..."
pipenv requirements --dev > requirements.txt

echo "Starting docker compose services..."
docker compose up -d --build

echo "Migrating the database..."
docker compose exec app python manage.py migrate

echo "Populating the data into tables..."
python dev_populate_data.py
