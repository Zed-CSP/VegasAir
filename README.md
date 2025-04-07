# VegasAir - Airline Booking Simulation

A full-stack application for airline booking simulation with dynamic pricing engine.

## Project Structure

```
vegasair/
├── backend/
│   ├── models/
│   │   ├── base.py
│   │   ├── flight.py
│   │   ├── booking.py
│   │   └── dynamic_price.py
│   ├── __init__.py
│   ├── main.py
│   └── database.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
- Create a new database named 'vegasair'
- Copy .env.example to .env and update the DATABASE_URL

4. Run the application:
```bash
uvicorn backend.main:app --reload
```

The API will be available at http://localhost:8000
API documentation will be available at http://localhost:8000/docs

## Features

- Flight management
- Dynamic pricing engine
- Booking system
- RESTful API
- PostgreSQL database
- FastAPI backend
- Next.js frontend (coming soon) 