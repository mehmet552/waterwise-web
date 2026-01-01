
import sqlite3
import os

def migrate_instance_db():
    db_path = os.path.join('instance', 'waterwise.db')
    print(f"Migrating database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add user_id column
        try:
            cursor.execute("ALTER TABLE consumption ADD COLUMN user_id INTEGER REFERENCES user(id)")
            print("Sütun eklendi: user_id")
        except sqlite3.OperationalError as e:
            print(f"Sütun zaten var veya hata: {e}")

        conn.commit()
    except Exception as e:
        print(f"Genel Hata: {e}")
    finally:
        conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate_instance_db()
