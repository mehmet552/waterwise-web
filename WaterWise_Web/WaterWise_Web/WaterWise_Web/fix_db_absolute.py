
import sqlite3
import os

def fix_specific_db():
    # Absolute path to the DB in the root 'instance' folder
    db_path = r"c:\Users\Mehmet\OneDrive\Masaüstü\waterwise güncel\instance\waterwise.db"
    
    print(f"Fixing database at: {db_path}")
    if not os.path.exists(db_path):
        print("❌ Database file not found at path.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'consumption'")
        row = cursor.fetchone()
        if not row:
             print("❌ Table 'consumption' not found.")
        else:
             tname = row[0]
             print(f"✅ Found table: {tname}")
             try:
                 cursor.execute(f"ALTER TABLE {tname} ADD COLUMN user_id INTEGER REFERENCES user(id)")
                 print(f"✅ Added 'user_id' column to {tname}")
             except sqlite3.OperationalError as e:
                 print(f"INFO: {e}")
                 
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_specific_db()
