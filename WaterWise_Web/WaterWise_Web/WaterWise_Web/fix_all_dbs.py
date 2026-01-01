
import sqlite3
import os

def upgrade_db(db_path):
    print(f"Checking database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Tablo adını bul (case insensitive)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'consumption'")
    row = cursor.fetchone()
    if not row:
        print(f"  ❌ Table 'consumption' not found in {db_path}")
        conn.close()
        return
        
    table_name = row[0]
    print(f"  ✅ Found table: {table_name}")
    
    # 2. Add user_id
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER REFERENCES user(id)")
        print(f"  ✅ Added column 'user_id' to {table_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
             print(f"  INFO: Column 'user_id' already exists in {table_name}")
        else:
             print(f"  ⚠️ Error adding column: {e}")
             
    conn.commit()
    conn.close()

def main():
    # Root dir
    if os.path.exists('waterwise.db'):
        upgrade_db('waterwise.db')
    else:
        print("No waterwise.db in root.")

    # Instance dir
    if os.path.exists(os.path.join('instance', 'waterwise.db')):
        upgrade_db(os.path.join('instance', 'waterwise.db'))
    else:
        print("No waterwise.db in instance/.")

if __name__ == "__main__":
    main()
