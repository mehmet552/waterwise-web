
import sqlite3

def check_db():
    print("Checking database...")
    try:
        conn = sqlite3.connect('waterwise.db')
        cursor = conn.cursor()
        
        print("Tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(tables)
        
        for table in tables:
            tname = table[0]
            print(f"\nColumns in {tname}:")
            cursor.execute(f"PRAGMA table_info({tname})")
            cols = cursor.fetchall()
            for c in cols:
                print(c)
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
