from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime

# Veritabanı nesnesini burada oluşturuyoruz (Henüz app'e bağlı değil)
db = SQLAlchemy()

# --- Kullanıcı Modeli ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # İlişki
    posts = db.relationship("Post", backref="user", lazy=True)

# --- Gönderi Modeli ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# --- Su Tüketim Modeli (YENİ) ---
class Consumption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False) # ISO Format YYYY-MM-DD
    category = db.Column(db.String(50), nullable=False)
    liters = db.Column(db.Float, nullable=False)
    # Yeni eklenen alanlar (Opsiyonel, geriye dönük uyumluluk için nullable)
    activity_type = db.Column(db.String(50), nullable=True) 
    amount = db.Column(db.Float, nullable=True)
    
    # İleride User ile ilişkilendirilebilir:
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

# --- Ayarlar Modeli (YENİ) ---
class Settings(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(200), nullable=False)

    @staticmethod
    def get_value(key, default=None):
        setting = Settings.query.get(key)
        return setting.value if setting else default

    @staticmethod
    def set_value(key, value):
        setting = Settings.query.get(key)
        if not setting:
            setting = Settings(key=key, value=str(value))
            db.session.add(setting)
        else:
            setting.value = str(value)
        db.session.commit()
