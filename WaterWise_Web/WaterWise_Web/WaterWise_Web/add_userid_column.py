
from app import app, db
import sqlite3

def add_userid_column():
    print("Migration: Adding user_id to consumption table...")
    conn = sqlite3.connect('waterwise.db')
    cursor = conn.cursor()
    
    try:
        try:
            cursor.execute("ALTER TABLE consumption ADD COLUMN user_id INTEGER REFERENCES user(id)")
            print("Sütun eklendi: user_id")
        except sqlite3.OperationalError as e:
            print(f"Sütun zaten olabilir: {e}")
            
        conn.commit()
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        conn.close()
    print("Migration tamamlandı.")

if __name__ == "__main__":
    add_userid_column()
