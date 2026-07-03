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
    # Check if column already exists
    cursor.execute("PRAGMA table_info(customer)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'whatsapp_notifications_enabled' not in columns:
        print("Adding 'whatsapp_notifications_enabled' column to 'customer' table...")
        cursor.execute("ALTER TABLE customer ADD COLUMN whatsapp_notifications_enabled BOOLEAN DEFAULT 1;")
        print("Column added successfully.")
    else:
        print("'whatsapp_notifications_enabled' column already exists.")

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
finally:
    conn.close()
