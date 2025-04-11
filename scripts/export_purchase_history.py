#!/usr/bin/env python3
import os
import sys
import csv
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.models.purchase_history import PurchaseHistory
from backend.db.database import SessionLocal, engine
from backend.config.config import settings

def export_purchase_history(output_dir: str = "data"):
    """
    Export all purchase history to a single CSV file.
    
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
            # Write header
            writer.writerow(['date', 'purchases', 'flight_number', 'class_type'])
            
            # Write data for all records
            for record in records:
                for date, purchases in record.daily_purchases.items():
                    writer.writerow([
                        date,
                        purchases,
                        record.flight_number,
                        record.class_type
                    ])
        
        print(f"Exported all purchase history to {filepath}")
            
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