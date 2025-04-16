#!/usr/bin/env python3
import os
import sys
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.models.purchase_history import PurchaseHistory
from backend.db.database import SessionLocal, engine
from backend.config.config import settings

def export_purchase_history(output_dir: str = "data"):
    """
    Export all purchase history to a single CSV file with enhanced time series features.
    
    Args:
        output_dir: Directory to save CSV file (will be created if doesn't exist)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output file path
    filepath = os.path.join(output_dir, "purchase_history.csv")
    
    # Get database session
    db = SessionLocal()
    try:
        # Get all purchase history records
        records = db.query(PurchaseHistory).all()
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header with enhanced features
            writer.writerow([
                'purchase_date',           # Actual calendar date of purchase
                'day_of_week',            # 0-6 (Monday-Sunday)
                'month',                   # 1-12
                'is_weekend',             # 0 or 1
                'days_until_departure',    # Original days until departure
                'purchases',               # Number of purchases
                'flight_number',           # Flight number
                'class_type',             # Cabin class
                'departure_date'           # Scheduled departure date
            ])
            
            # Write data for all records
            for record in records:
                departure_date = record.departure_date
                for days_until_departure, purchases in record.daily_purchases.items():
                    # Calculate actual purchase date
                    days_until = int(days_until_departure)
                    purchase_date = departure_date - timedelta(days=days_until)
                    
                    # Calculate additional time features
                    is_weekend = 1 if purchase_date.weekday() >= 5 else 0
                    
                    writer.writerow([
                        purchase_date.strftime('%Y-%m-%d'),
                        purchase_date.weekday(),
                        purchase_date.month,
                        is_weekend,
                        days_until_departure,
                        purchases,
                        record.flight_number,
                        record.class_type,
                        departure_date.strftime('%Y-%m-%d %H:%M:%S')
                    ])
        
        print(f"Exported enhanced purchase history to {filepath}")
            
    finally:
        db.close()

def main():
    """Main entry point for the script."""
    try:
        # Default to 'data' directory in project root
        output_dir = os.path.join(project_root, 'data')
        
        # Export the data
        export_purchase_history(output_dir)
        print("Export completed successfully!")
        
    except Exception as e:
        print(f"Error exporting purchase history: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 