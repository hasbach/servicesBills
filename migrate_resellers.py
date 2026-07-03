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
    # 1. Create Reseller table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reseller (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        type VARCHAR(20) NOT NULL,
        balance FLOAT DEFAULT 0.0
    );
    ''')
    print("Created 'reseller' table (if it didn't exist).")

    # 2. Create ResellerPayment table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reseller_payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reseller_id INTEGER NOT NULL,
        amount FLOAT NOT NULL,
        type VARCHAR(50) NOT NULL,
        date DATETIME NOT NULL,
        description VARCHAR(200),
        FOREIGN KEY(reseller_id) REFERENCES reseller(id)
    );
    ''')
    print("Created 'reseller_payment' table (if it didn't exist).")

    # 3. Add reseller_id to customer table
    cursor.execute("PRAGMA table_info(customer)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'reseller_id' not in columns:
        cursor.execute("ALTER TABLE customer ADD COLUMN reseller_id INTEGER REFERENCES reseller(id);")
        print("Added 'reseller_id' column to 'customer' table.")
    else:
        print("'reseller_id' column already exists in 'customer'.")

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
finally:
    conn.close()
