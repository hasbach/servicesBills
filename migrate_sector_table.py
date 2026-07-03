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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sector (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE
    );
    ''')
    print("Created 'sector' table.")

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
finally:
    conn.close()
