from app import app, db
from models import User, Post, Consumption, Settings
import sqlite3

def migrate_database():
    print("Veritabanı migration işlemi başlıyor...")
    
    # 1. waterwise.db'ye bağlan ve eksik sütunları ekle
    conn = sqlite3.connect('waterwise.db')
    cursor = conn.cursor()
    
    try:
        # activity_type sütunu ekle
        try:
            cursor.execute("ALTER TABLE consumption ADD COLUMN activity_type TEXT")
            print("Sütun eklendi: activity_type")
        except sqlite3.OperationalError:
            print("Sütun zaten var: activity_type")
            
        # amount sütunu ekle
        try:
            cursor.execute("ALTER TABLE consumption ADD COLUMN amount REAL")
            print("Sütun eklendi: amount")
        except sqlite3.OperationalError:
            print("Sütun zaten var: amount")
            
        conn.commit()
    except Exception as e:
        print(f"Hata oluştu (Alter Table): {e}")
    finally:
        conn.close()

    # 2. SQLAlchemy ile eksik tabloları (User, Post) oluştur
    # app.config'i geçici olarak waterwise.db yapmamız lazım, 
    # ama app.py zaten modify edilecek, bu script çalıştırılmadan önce app.py'yi güncellemeliyim.
    # Veya context içinde config override yapılabilir.
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///waterwise.db'
    
    with app.app_context():
        # Tabloları oluştur (User, Post yoksa oluşur, Consumption varsa dokunmaz)
        db.create_all()
        print("Eksik tablolar (User, Post) oluşturuldu.")
        
        # Eğer community.db'den veri taşınacaksa buraya eklenebilir
        # Ancak kullanıcı veri kaybından bahsettiği için öncelik waterwise.db'yi korumak.
        
    print("Migration tamamlandı.")

if __name__ == "__main__":
    migrate_database()
