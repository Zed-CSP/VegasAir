#!/bin/bash

# Drop PostgreSQL database if it exists
echo "Dropping database if it exists..."
psql -U postgres -c "DROP DATABASE IF EXISTS vegasair;"

# Create PostgreSQL database
echo "Creating database..."
psql -U postgres -c "CREATE DATABASE vegasair;"

# Run the database initialization script
echo "Running database initialization script..."
python3 -m backend.db.init_db

echo "Database reset complete!" 