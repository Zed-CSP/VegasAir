#!/bin/bash

# Create PostgreSQL database if it doesn't exist
echo "Creating database if it doesn't exist..."
psql -U postgres -c "CREATE DATABASE vegasair;" || true

# Run the database initialization script
echo "Running database initialization script..."
python3 -m backend.db.init_db

echo "Database initialization complete!" 