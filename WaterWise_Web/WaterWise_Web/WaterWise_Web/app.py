from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
# ÖNEMLİ: Veritabanını ve Modelleri models.py'den çekiyoruz
# ARTIK models.py içindeki Consumption ve Settings'i kullanıyoruz
from models import db, User, Post, Consumption, Settings
from utils import calculate_water_usage, get_activity_label
import datetime
# import pandas as pd # Lazy loaded in report_data
import random
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# import re -> re kalsın, standart kütüphane
import re

# === KÜTÜPHANELERİ ÖNCEDEN YÜKLE (Cold Start Önlemi) ===
try:
    import cv2
    import pytesseract
    import numpy as np
    import pandas as pd
    # Tesseract yolunu burada tanımlayalım
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError as e:
    print(f"Kütüphane Hatası: {e}")

# --- Flask uygulamasını oluştur ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-fallback'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///waterwise.db'

# === VERİTABANI BAĞLANTISI ===
db.init_app(app) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "community.login" 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === Blueprint ve Tablo Oluşturma ===
with app.app_context():
    try:
        from community_routes import community
        app.register_blueprint(community, url_prefix='/community')
        db.create_all() # Tabloları veritabanında oluştur (Consumption ve Settings dahil)
    except ImportError:
        print("UYARI: community_routes.py bulunamadı, topluluk özellikleri çalışmayabilir.")
    except Exception as e:
        print(f"HATA: {e}")

# === ANA SAYFA ===
@app.route('/')
def index():
    return render_template('index.html')

# === API ENDPOINTS (SU TAKİBİ - GÜNCELLENDİ) ===

@app.route('/api/add', methods=['POST'])
def add_consumption():
    data = request.json
    try:
        # Yeni Aktivite Mantığı
        activity = data.get('activity', 'custom') # Varsayılan: custom
        amount = float(data.get('amount', 0))
        
        # Eğer eski arayüzden sadece "liters" geliyorsa onu destekle
        if 'liters' in data and 'activity' not in data:
            activity = 'custom'
            amount = float(data['liters'])

        # Hesaplama
        liters = calculate_water_usage(activity, amount)
        category_label = get_activity_label(activity)
        
        today_date = datetime.date.today().isoformat()
        
        # Kullanıcı ID Belirleme
        user_id = current_user.id if current_user.is_authenticated else None

        # Veritabanına Kayıt (SQLAlchemy)
        new_record = Consumption(
            date=today_date,
            category=category_label,
            liters=liters,
            activity_type=activity,
            amount=amount,
            user_id=user_id
        )
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Veri eklendi: {liters:.1f} Litre ({category_label})"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/target', methods=['GET', 'POST'])
def handle_target():
    if request.method == 'POST':
        data = request.json
        try:
            target = float(data['target'])
            # Veritabanı Güncelleme (SQLAlchemy)
            Settings.set_value('daily_target', target)
            return jsonify({"success": True, "new_target": target})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    else:
        # Veritabanından Oku
        target = float(Settings.get_value('daily_target', 150))
        return jsonify({"daily_target": target})

@app.route('/api/today_status')
def today_status():
    today_date = datetime.date.today().isoformat()
    uid = current_user.id if current_user.is_authenticated else None
    
    # ORM ile Bugünün Toplamı (Faturalar Hariç)
    # activity_type != 'bill'
    result = db.session.query(db.func.sum(Consumption.liters)).filter_by(date=today_date, user_id=uid).filter(Consumption.activity_type != 'bill').scalar()
    today_total = result if result else 0
    
    target = float(Settings.get_value('daily_target', 150))
    target = float(Settings.get_value('daily_target', 150))
    return jsonify({"today_total": today_total, "daily_target": target})

@app.route('/api/reset_today', methods=['POST'])
def reset_today():
    try:
        today_date = datetime.date.today().isoformat()
        uid = current_user.id if current_user.is_authenticated else None
        
        # Bugünün verilerini sil
        Consumption.query.filter_by(date=today_date, user_id=uid).delete()
        db.session.commit()
        return jsonify({"success": True, "message": "Bugünün verileri sıfırlandı."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/report_data')
def report_data():
    period = request.args.get('period', 'daily') # daily, weekly, monthly
    
    today = pd.Timestamp.now().normalize()
    uid = current_user.id if current_user.is_authenticated else None
    
    # ORM ile Tüm Verileri Çek
    all_data = Consumption.query.filter_by(user_id=uid).order_by(Consumption.date).all()
    target = float(Settings.get_value('daily_target', 150))
    
    if not all_data:
        return jsonify({"daily_trend": {}, "category_pie": {}})

    # Pandas DataFrame'e dönüştür
    # activity_type alanını da eklemeliyiz ki filtreleme yapabilelim
    data_list = [{'id': d.id, 'date': d.date, 'category': d.category, 'liters': d.liters, 'activity_type': d.activity_type} for d in all_data]
    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    
    # Kategori Toplamları (Her zaman tüm zamanların toplamı veya o periyodun toplamı olabilir, şimdilik tüm zamanlar kalsın veya periyoda göre filtreleyelim)
    # Basitlik için kategori dağılımını "Seçilen Periyodun Toplamı" olarak yapmak daha mantıklı olurdu ama 
    # şimdilik tüm zamanlar kalsın, kullanıcı o anki grafiğe odaklansın.
    
    # --- Tarih Filtreleme ve Gruplama ---
    today = pd.Timestamp.now().normalize()
    filtered_df = df.copy()
    trend_labels = []
    trend_data = []
    trend_target = target

    if period == 'monthly':
        # Son 12 Ay (Tam Liste)
        end_date = today
        start_date = end_date - pd.DateOffset(months=11)
        full_idx = pd.date_range(start=start_date, end=end_date, freq='MS')
        
        # Filtreleme (Geniş tutalım)
        filtered_df = df[df['date'] >= start_date]

        # Aylık Toplamlar ve Reindex
        # 'MS' = Month Start (Ayın 1'i)
        monthly_grp = filtered_df.set_index('date').resample('MS')['liters'].sum()
        monthly_grp = monthly_grp.reindex(full_idx, fill_value=0)
        
        trend_labels = monthly_grp.index.strftime('%Y-%m').tolist()
        trend_data = monthly_grp.values.tolist()
        trend_target = target * 30 

    elif period == 'weekly':
        # Son 12 Hafta
        end_date = today
        start_date = end_date - pd.DateOffset(weeks=11) 
        # Haftalık (Pazartesi başlangıç)
        full_idx = pd.date_range(start=start_date, end=end_date, freq='W-MON')
        
        filtered_df = df[df['date'] >= start_date]
        
        weekly_grp = filtered_df.set_index('date').resample('W-MON')['liters'].sum()
        weekly_grp = weekly_grp.reindex(full_idx, fill_value=0)
        
        trend_labels = weekly_grp.index.strftime('Hafta %U').tolist()
        trend_data = weekly_grp.values.tolist()
        trend_target = target * 7 

    else: # daily
        # Son 30 Gün
        end_date = today
        start_date = end_date - pd.DateOffset(days=29)
        full_idx = pd.date_range(start=start_date, end=end_date, freq='D')
        
        filtered_df = df[df['date'] >= (start_date - pd.Timedelta(days=1))] # Saat farkı için opsiyonel buffer
        
        # Günlük Toplamlar ve Reindex
        daily_grp = filtered_df.groupby(filtered_df['date'].dt.normalize())['liters'].sum()
        daily_grp = daily_grp.reindex(full_idx, fill_value=0)
        
        trend_labels = daily_grp.index.strftime('%Y-%m-%d').tolist()
        trend_data = daily_grp.values.tolist()
        
    # Kategori Dağılımını sadece bu filtrelenmiş veriye ve Fatura HARİÇ veriye göre yap
    # Trend Grafiği de Fatura hariç olmalı
    # activity_type kontrolü yapıyoruz (Eski verilerde None olabilir, o yüzden 'or' kullanıyoruz)
    
    # Fatura Hariç DataFrame
    chart_df = filtered_df[filtered_df['activity_type'] != 'bill']
    
    # Eğer activity_type null ise ve category 'Fatura Bildirimi' ise onu da çıkar
    chart_df = chart_df[chart_df['category'] != 'Fatura Bildirimi']

    # --- Trend Yeniden Hesaplama (Reindex chart_df üzerinden) ---
    if period == 'monthly':
        monthly_grp = chart_df.set_index('date').resample('MS')['liters'].sum()
        monthly_grp = monthly_grp.reindex(full_idx, fill_value=0)
        trend_data = monthly_grp.values.tolist() # Labels zaten aynı
        
    elif period == 'weekly':
        weekly_grp = chart_df.set_index('date').resample('W-MON')['liters'].sum()
        weekly_grp = weekly_grp.reindex(full_idx, fill_value=0)
        trend_data = weekly_grp.values.tolist()
        
    else: # daily
        daily_grp = chart_df.groupby(chart_df['date'].dt.normalize())['liters'].sum()
        daily_grp = daily_grp.reindex(full_idx, fill_value=0)
        trend_data = daily_grp.values.tolist()

    category_totals = chart_df.groupby('category')['liters'].sum()
    
    # --- Fatura Geçmişi (Ayrı Veri) ---
    # Tüm zamanlardan son 5 faturayı çek
    bills_df = df[(df['activity_type'] == 'bill') | (df['category'] == 'Fatura Bildirimi')]
    bills_data = bills_df.sort_values('date', ascending=False).head(5)[['id', 'date', 'liters']].to_dict('records')
    # Tarihi string yap
    for b in bills_data:
        b['date'] = b['date'].strftime('%Y-%m-%d')
        b['amount_m3'] = round(b['liters'] / 1000, 2)

    return jsonify({
        "daily_trend": {
            "labels": trend_labels,
            "data": trend_data,
            "target": trend_target
        },
        "category_pie": {
            "labels": category_totals.index.tolist(),
            "data": category_totals.values.tolist()
        },
        "bill_history": bills_data
    })

@app.route('/api/delete_consumption/<int:id>', methods=['DELETE'])
def delete_consumption(id):
    try:
        uid = current_user.id if current_user.is_authenticated else None
        record = Consumption.query.get(id)
        
        if record:
            # Sadece kendi kaydını veya anonimse anonim kaydı silebilir
            if record.user_id != uid:
                return jsonify({'success': False, 'message': 'Bu kaydı silme yetkiniz yok.'}), 403
                
            db.session.delete(record)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Kayıt silindi.'})
        else:
            return jsonify({'success': False, 'message': 'Kayıt bulunamadı.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/summary')
def get_summary():
    try:
        uid = current_user.id if current_user.is_authenticated else None
        today = datetime.date.today()
        
        # --- HAFTALIK KARŞILAŞTIRMA ---
        seven_days_ago = today - datetime.timedelta(days=7)
        fourteen_days_ago = today - datetime.timedelta(days=14)
        
        recent_week_total = db.session.query(db.func.sum(Consumption.liters))\
            .filter(Consumption.date > seven_days_ago.isoformat())\
            .filter(Consumption.activity_type != 'bill')\
            .filter(Consumption.user_id == uid)\
            .scalar() or 0
            
        previous_week_total = db.session.query(db.func.sum(Consumption.liters))\
            .filter(Consumption.date <= seven_days_ago.isoformat())\
            .filter(Consumption.date > fourteen_days_ago.isoformat())\
            .filter(Consumption.activity_type != 'bill')\
            .filter(Consumption.user_id == uid)\
            .scalar() or 0
            
        # --- AYLIK KARŞILAŞTIRMA (Basit yaklaşım: Bu ay vs Geçen Ay) ---
        # Bu ayın başı
        this_month_start = today.replace(day=1)
        # Geçen ayın başı
        last_month_end = this_month_start - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        this_month_total = db.session.query(db.func.sum(Consumption.liters))\
            .filter(Consumption.date >= this_month_start.isoformat())\
            .filter(Consumption.activity_type != 'bill')\
            .filter(Consumption.user_id == uid)\
            .scalar() or 0

        last_month_total = db.session.query(db.func.sum(Consumption.liters))\
            .filter(Consumption.date >= last_month_start.isoformat())\
            .filter(Consumption.date < this_month_start.isoformat())\
            .filter(Consumption.activity_type != 'bill')\
            .filter(Consumption.user_id == uid)\
            .scalar() or 0

        # Karşılaştırma Metni Seçimi
        # Eğer bu ayın verisi yeterliyse aylık konuş, yoksa haftalık.
        comparison_text = "Veri analizi yapılıyor..."
        
        # Öncelik stratejisi:
        # Eğer son 1 haftada veri varsa haftalık analiz ver.
        # Eğer ayın ortasındaysak ve veri varsa aylık analiz de ekle.
        
        # Şimdilik varsayılan haftalık analiz
        if previous_week_total > 0:
            diff = recent_week_total - previous_week_total
            percent = (diff / previous_week_total) * 100
            if diff < 0:
                comparison_text = f"Geçen haftaya göre <span style='color:var(--status-good); font-weight:bold'>%{abs(percent):.0f} daha az</span> su harcadın! 📉"
            else:
                comparison_text = f"Geçen haftaya göre <span style='color:var(--status-bad); font-weight:bold'>%{abs(percent):.0f} daha fazla</span> su harcadın. 📈"
        
        # Eğer ayın 15'inden sonraysa ve geçen ay veri varsa, aylık analizi de ekle veya değiştir
        if today.day > 10 and last_month_total > 0:
             diff_m = this_month_total - last_month_total
             # Oranlama: Bu ayın şu ana kadarki gün sayısı ile geçen ayın tamamını kıyaslamak adil olmaz.
             # Bu yüzden basitçe "Geçen ay toplam X harcamışken bu ay şimdiden Y harcadın" gibi gidelim
             # Veya ortalama üzerinden gidelim.
             
             # Günlük ortalama üzerinden kıyas
             days_in_this_month = today.day
             # Geçen ayın gün sayısı (yaklaşık 30)
             days_in_last_month = last_month_end.day
             
             avg_this = this_month_total / days_in_this_month
             avg_last = last_month_total / days_in_last_month
             
             if avg_last > 0:
                 diff_avg = avg_this - avg_last
                 percent_avg = (diff_avg / avg_last) * 100
                 
                 extra_msg = ""
                 if diff_avg < 0:
                     extra_msg = f"<br>Bu ay ortalaman geçen aydan <span style='color:var(--status-good)'>%{abs(percent_avg):.0f} daha iyi</span> gidiyor. 📅"
                 else:
                     extra_msg = f"<br>Bu ay ortalaman geçen aydan <span style='color:var(--status-bad)'>%{abs(percent_avg):.0f} daha yüksek</span>. 📅"
                 
                 comparison_text += extra_msg

        elif recent_week_total == 0 and previous_week_total == 0:
             comparison_text = "Henüz yeterli veri yok. Kayıt eklemeye başla! 🚀"

        # En Çok Harcanan Kategori
        top_cat = db.session.query(Consumption.category, db.func.sum(Consumption.liters))\
            .filter(Consumption.activity_type != 'bill')\
            .filter(Consumption.user_id == uid)\
            .group_by(Consumption.category)\
            .order_by(db.func.sum(Consumption.liters).desc())\
            .first()
            
        top_category_text = ""
        if top_cat:
            top_category_text = f"En çok suyu <strong>{top_cat[0]}</strong> ({top_cat[1]:.0f} L) kategorisinde harcadın."

        return jsonify({
            "week_comparison_text": comparison_text, 
            "top_category_text": top_category_text
        })
    except Exception as e:
        print(f"Summary Error: {e}")
        return jsonify({"week_comparison_text": "Analiz hatası.", "top_category_text": ""}), 500

@app.route('/api/streak')
def get_streak():
    return jsonify({"streak": 0})

# ==================================================
# === FATURA ANALİZİ (OCR) ===
# ==================================================
@app.route('/api/analyze_bill', methods=['POST'])
def analyze_bill():
    if 'file' not in request.files: return jsonify({'success': False, 'message': 'Dosya yok'})
    file = request.files['file']
    
    try:
        # cv2, pytesseract vb. yukarıda yüklendi
        
        filestr = file.read()
        npimg = np.frombuffer(filestr, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        text = pytesseract.image_to_string(text_img, lang='eng', config='--oem 3 --psm 6')

        # Regex ile veri yakalama
        found_val = None
        calculation_method = "Doğrudan Okuma"
        
        match_total = re.search(r'(?:Toplam|Topiam|Tuketim).*?(?:m3|mm|m\S).*?(\d+)', text, re.IGNORECASE)
        match_daily = re.search(r'(?:GUniUk|Gunluk).*?(\d+[.,]\d+)', text, re.IGNORECASE)
        # Regex Güncellemesi: Multiline, Türkçe ve OCR Hataları (ODENECER vb)
        # Regex Güncellemesi: Multiline, Türkçe ve OCR Hataları (ODENECER vb)
        # Kullanıcının "Ödenecek Tutar" uyarısı üzerine düzeltildi:
        # [ ] yerine (?: ) kullanıldı ve aradaki boşluk/satır atlama esnekleştirildi.
        match_price = re.search(r'(?:ödenecek\s*tu|odenecek\s*tu|odenecer\s*tu|TUTAR|genel).*?(\d+[.,]?\d*)', text, re.IGNORECASE | re.DOTALL)
        
        if match_price:
            print(f"DEBUG: Price Match Found: {match_price.group(1)}")
            try:
                price_str = match_price.group(1).replace(',', '.')
                found_val = solve_usage_from_price(float(price_str))
                calculation_method = f"Fatura Tutarından Hesaplama ({price_str} TL)"
            except: pass
            
        # 2.1. Fallback: Eğer spesifik "Ödenecek Tutar" bulunamazsa, sayfadaki EN BÜYÜK TL değerini al
        if not found_val:
            print("DEBUG: Specific Price Match Failed - Trying Max TL Heuristic")
            # Tüm "Sayı TL" formatlarını bul
            all_prices = re.findall(r'(\d+[.,]\d+)\s*(?:TL|T1|TI)', text, re.IGNORECASE)
            print(f"DEBUG: Found Prices: {all_prices}")
            
            valid_prices = []
            for p_str in all_prices:
                try:
                    # Virgül/Nokta düzeltmesi (Avrupa/TR formatı: 715,00 -> 715.00)
                    # 1.000,50 gibi durumlar için basit replace yetmez ama basit faturalar için replace(',', '.') yeterli
                    val = float(p_str.replace(',', '.'))
                    valid_prices.append(val)
                except: continue
            
            if valid_prices:
                max_price = max(valid_prices)
                if max_price > 10: # 10 TL'den küçükse muhtemelen hatalıdır veya küsurattır
                    print(f"DEBUG: Using Max Price: {max_price}")
                    from utils import solve_usage_from_price
                    found_val = solve_usage_from_price(max_price)
                    calculation_method = f"Fatura Tutarından (Tahmin: {max_price} TL)"

        # 3. Senaryo: Günlük Ortalamadan Tahmin (Düşük Öncelik)
        if not found_val and match_daily:
            found_val = round(float(match_daily.group(1).replace(',', '.')) * 30, 2)
            calculation_method = "Günlük Ortalamadan Tahmin"

        if found_val:
            liters_total = found_val * 1000
            daily_avg = liters_total / 30
            
            # db_handler yerine Settings modelini kullanıyoruz
            try:
                user_target = float(Settings.get_value('daily_target', 150))
            except:
                user_target = 150
            
            # Durum Değerlendirmesi
            usage_ratio = (daily_avg / user_target) * 100
            
            status, advice_title = "active", "Durum Analizi"
            advice_text = ""

            if daily_avg > (user_target * 1.5):
                status = "danger"
                advice_title = "Yüksek Tüketim"
                advice_text = f"Günlük ortalama ({daily_avg:.0f} L) belirlenen hedefin çok üzerinde (%{usage_ratio:.0f}). Tasarruf önlemleri almanız önerilir."
            elif daily_avg > user_target:
                status = "warning"
                advice_title = "Hedef Aşımı"
                advice_text = f"Günlük ortalama ({daily_avg:.0f} L) hedefinizi aşıyor (%{usage_ratio:.0f}). Daha dikkatli kullanım gerekebilir."
            else:
                status = "success"
                advice_title = "İdeal Tüketim"
                advice_text = f"Günlük tüketim ({daily_avg:.0f} L) hedef sınırları içerisinde (%{usage_ratio:.0f}). Verimli kullanımınız için teşekkürler."
            
            # Fiyat bazlı tahmin uyarısı
            if "Fatura Tutarından" in calculation_method:
                advice_text += "<br><small><i>*Bu hesaplama fatura tutarından tahmin edilmiştir, gerçek sayaç değeriyle farklılık gösterebilir.</i></small>"

            return jsonify({
                'success': True, 
                'liters': liters_total,
                'daily_avg': daily_avg,
                'status': status,
                'advice_title': advice_title,
                'advice_text': advice_text,
                'message': f"Fatura: {found_val} m³ ({calculation_method})"
            })
        else:
            # DEBUG BİLGİSİ İLE DÖN
            debug_msg = "Değer okunamadı. "
            if match_price: debug_msg += f"Fiyat bulundu ancak hesaplanamadı ({match_price.group(1)}). "
            else: debug_msg += "Fiyat bulunamadı. "
            
            debug_msg += f"OCR İlk 50 Karakter: {text[:50]}..."
            return jsonify({'success': False, 'message': debug_msg})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Hata: {str(e)}'})

# ==================================================
# === HAVA DURUMU API ===
# ==================================================
@app.route('/api/weather_advice')
def weather_advice():
    city = "Istanbul"
    api_key = os.environ.get('WEATHER_API_KEY') 

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=tr"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        if data.get('cod') != 200: raise Exception("API Hatası")

        weather = data.get('weather', [{}])[0]
        main = data.get('main', {})
        temp = main.get('temp')
        description = weather.get('description', '').capitalize()

        if temp > 30: advice = "Bugün çok sıcak 🌞 Bahçe sulamasını sabah erken saatlerde yap!"
        elif temp < 10: advice = "Soğuk hava ❄️ Boruların donmamasına dikkat et!"
        elif "yağmur" in description.lower(): advice = "Yağmur bekleniyor ☔ Bitkileri sulamana gerek yok!"
        else: advice = "Su tasarrufu için muslukları kısa süreli kullan 💧"

        return jsonify({"city": city, "temp": temp, "advice": advice})

    except Exception as e:
        return jsonify({"city": city, "temp": "-", "advice": "Veri alınamadı."})

# === İPUÇLARI SAYFASI ===
@app.route('/tips')
def tips():
    return render_template('tips.html', random_tip="Musluğu kapatmayı unutma!")

# === ÇALIŞTIR ===
@app.route('/api/calculate_cost', methods=['POST'])
def api_calculate_cost():
    data = request.json
    usage_m3 = float(data.get('usage', 0))
    user_type = data.get('user_type', 'residential')
    
    manual_rates = None
    if data.get('manual', False):
        try:
            manual_rates = {
                'water_tier1': float(data.get('water_tier1')),
                'waste_tier1': float(data.get('waste_tier1'))
                # Diğer tier'ları da isterse ekleyebiliriz, şimdilik en temeli bu
            }
        except:
            pass # Hatalı giriş varsa varsayılanı kullan
            
    from utils import calculate_iski_bill
    result = calculate_iski_bill(usage_m3, user_type, manual_rates)
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/estimate_usage_from_price', methods=['POST'])
def api_estimate_usage():
    data = request.json
    price = float(data.get('price', 0))
    user_type = data.get('user_type', 'residential')
    
    from utils import solve_usage_from_price
    usage_m3 = solve_usage_from_price(price, user_type)
    
    return jsonify({'success': True, 'usage_m3': usage_m3, 'liters': usage_m3 * 1000})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)