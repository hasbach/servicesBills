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
    print("Starting live server database migration...")

    # 1. Create Reseller table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reseller (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        type VARCHAR(20) NOT NULL DEFAULT 'credit',
        balance FLOAT DEFAULT 0.0,
        address VARCHAR(200),
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    print("Checked/Created 'reseller' table.")

    # 2. Create ResellerPayment table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reseller_payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reseller_id INTEGER NOT NULL REFERENCES reseller(id),
        amount FLOAT NOT NULL,
        payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        payment_method VARCHAR(50),
        notes TEXT
    );
    ''')
    print("Checked/Created 'reseller_payment' table.")

    # 3. Add reseller_id to Customer and Payment (if they don't exist)
    # Using pragma table_info to check columns
    cursor.execute("PRAGMA table_info(customer)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'reseller_id' not in columns:
        cursor.execute('ALTER TABLE customer ADD COLUMN reseller_id INTEGER REFERENCES reseller(id)')
        print("Added 'reseller_id' to 'customer' table.")

    cursor.execute("PRAGMA table_info(payment)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'reseller_id' not in columns:
        cursor.execute('ALTER TABLE payment ADD COLUMN reseller_id INTEGER REFERENCES reseller(id)')
        print("Added 'reseller_id' to 'payment' table.")
    if 'collected_amount' not in columns:
        cursor.execute('ALTER TABLE payment ADD COLUMN collected_amount FLOAT')
        print("Added 'collected_amount' to 'payment' table.")

    # 4. Add sector column to Customer (if it doesn't exist)
    cursor.execute("PRAGMA table_info(customer)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'sector' not in columns:
        cursor.execute('ALTER TABLE customer ADD COLUMN sector VARCHAR(100)')
        print("Added 'sector' to 'customer' table.")

    # 5. Create Sector table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sector (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE
    );
    ''')
    print("Checked/Created 'sector' table.")

    # 6. Create Supplier table
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
    print("Checked/Created 'supplier' table.")

    # 7. Create SupplierPayment table
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
    print("Checked/Created 'supplier_payment' table.")

    # 8. Add is_credit and supplier_id to Expense
    cursor.execute("PRAGMA table_info(expense)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_credit' not in columns:
        cursor.execute("ALTER TABLE expense ADD COLUMN is_credit BOOLEAN DEFAULT 0")
        print("Added 'is_credit' to 'expense'")
    if 'supplier_id' not in columns:
        cursor.execute("ALTER TABLE expense ADD COLUMN supplier_id INTEGER REFERENCES supplier(id)")
        print("Added 'supplier_id' to 'expense'")

    # 9. Fix empty string reseller_ids
    print("Fixing any corrupt empty string reseller_ids...")
    cursor.execute("UPDATE customer SET reseller_id = NULL WHERE reseller_id = '' OR reseller_id = ' '")
    rows_customer = cursor.rowcount
    
    cursor.execute("UPDATE payment SET reseller_id = NULL WHERE reseller_id = '' OR reseller_id = ' '")
    rows_payment = cursor.rowcount
    
    print(f"Fixed {rows_customer} customer records and {rows_payment} payment records.")

    conn.commit()
    print("Migration completed successfully!")

except Exception as e:
    conn.rollback()
    print(f"Migration failed: {e}")
finally:
    conn.close()
