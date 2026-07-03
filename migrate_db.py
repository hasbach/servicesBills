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
    cursor.execute("PRAGMA table_info(payment)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'paid_at' not in columns:
        print("Adding 'paid_at' column to 'payment' table...")
        cursor.execute("ALTER TABLE payment ADD COLUMN paid_at DATETIME;")
        print("Column added successfully.")
    else:
        print("'paid_at' column already exists.")

    # Backfill the 'paid_at' date with the original 'date' for payments that are already marked as paid
    print("Backfilling 'paid_at' for existing paid payments...")
    cursor.execute("UPDATE payment SET paid_at = date WHERE paid = 1 AND paid_at IS NULL;")
    backfill_count = cursor.rowcount
    print(f"Successfully backfilled {backfill_count} payment(s).")
    
    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
finally:
    conn.close()
