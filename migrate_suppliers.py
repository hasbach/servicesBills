import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Migrating Supplier tables...")
    
    # 1. Create Supplier table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supplier (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20),
        balance FLOAT DEFAULT 0.0,
        address VARCHAR(200),
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 2. Create SupplierPayment table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supplier_payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL REFERENCES supplier(id),
        amount FLOAT NOT NULL,
        payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        payment_method VARCHAR(50),
        reference_note TEXT
    );
    ''')

    # 3. Add columns to Expense table
    cursor.execute("PRAGMA table_info(expense)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_credit' not in columns:
        cursor.execute("ALTER TABLE expense ADD COLUMN is_credit BOOLEAN DEFAULT 0")
        print("Added 'is_credit' to 'expense'")
        
    if 'supplier_id' not in columns:
        cursor.execute("ALTER TABLE expense ADD COLUMN supplier_id INTEGER REFERENCES supplier(id)")
        print("Added 'supplier_id' to 'expense'")

    conn.commit()
    print("Migration completed successfully!")
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
