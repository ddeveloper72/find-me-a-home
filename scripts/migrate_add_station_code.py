"""
Add station_code column to transport_stations table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
import sqlite3

def main():
    with app.app_context():
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'findmehome.db')
        
        print(f"Database path: {db_path}")
        print("Adding station_code column to transport_stations table...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(transport_stations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'station_code' in columns:
            print("Column 'station_code' already exists!")
        else:
            cursor.execute("ALTER TABLE transport_stations ADD COLUMN station_code VARCHAR(50)")
            conn.commit()
            print("✓ Column 'station_code' added successfully!")
        
        conn.close()
        print("\nDatabase migration complete.")
        print("Now run: .venv\\Scripts\\python.exe scripts/add_stop_codes.py")

if __name__ == '__main__':
    main()
