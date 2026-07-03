import sqlite3

def migrate():
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()

    # 1. Add fields to Payment
    payment_cols = [
        ('collected', 'BOOLEAN DEFAULT 0'),
        ('collected_at', 'DATETIME'),
        ('collected_by_id', 'INTEGER REFERENCES user(id)'),
        ('received_by_id', 'INTEGER REFERENCES user(id)')
    ]
    
    for col, ctype in payment_cols:
        try:
            cursor.execute(f'ALTER TABLE payment ADD COLUMN {col} {ctype};')
            print(f"Added {col} to payment")
        except sqlite3.OperationalError as e:
            print(f"Skipped {col} on payment: {e}")

    # 2. Create TicketLog table
    try:
        cursor.execute('''
            CREATE TABLE ticket_log (
                id INTEGER PRIMARY KEY,
                ticket_id INTEGER NOT NULL REFERENCES support_ticket(id),
                user_id INTEGER NOT NULL REFERENCES user(id),
                action VARCHAR(50) NOT NULL,
                details TEXT,
                timestamp DATETIME NOT NULL
            )
        ''')
        print("Created ticket_log table")
    except sqlite3.OperationalError as e:
        print(f"Skipped ticket_log table: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
