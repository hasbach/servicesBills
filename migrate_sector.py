import sqlite3
import os
import sys

# Connect to the SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add sector to customer table
    cursor.execute("PRAGMA table_info(customer)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'sector' not in columns:
        cursor.execute("ALTER TABLE customer ADD COLUMN sector VARCHAR(100);")
        print("Added 'sector' column to 'customer' table.")
    else:
        print("'sector' column already exists in 'customer'.")

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
finally:
    conn.close()
