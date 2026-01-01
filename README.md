# WaterWise Web 💧

**WaterWise Web**, su tüketiminizi takip etmenize, faturalarınızı analiz etmenize ve su tasarrufu yapmanıza yardımcı olan akıllı bir web uygulamasıdır.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Özellikler

- **📊 Su Tüketimi Takibi:** Günlük aktiviteler (duş, bulaşık, çamaşır vb.) bazında su kullanımınızı kaydedin.
- **🧾 Fatura Analizi (OCR):** Su faturanızın fotoğrafını yükleyin, yapay zeka (OCR) ile tüketim ve tutar verilerini otomatik çekin.
- **📈 Görsel Raporlar:** Günlük, haftalık ve aylık tüketim grafiklerinizi inceleyin.
- **🏆 Lider Tablosu:** Topluluktaki diğer kullanıcılarla yarışın ve tasarruf yaparak üst sıralara çıkın.
- **💡 Akıllı İpuçları:** Hava durumu (API) ve kullanım alışkanlıklarınıza göre size özel tasarruf önerileri alın.

## 🚀 Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

1.  **Gereksinimleri Yükleyin:**
    ```bash
    pip install -r WaterWise_Web/WaterWise_Web/WaterWise_Web/requirements.txt
    ```

2.  **Çevre Değişkenlerini Ayarlayın:**
    `WaterWise_Web/WaterWise_Web/WaterWise_Web/` klasörü içinde `.env` dosyası oluşturun ve gerekli API anahtarlarını ekleyin (Örnek: `WEATHER_API_KEY`).

3.  **Uygulamayı Başlatın:**
    ```bash
    cd WaterWise_Web/WaterWise_Web/WaterWise_Web
    python app.py
    ```
4.  Tarayıcınızda `http://127.0.0.1:5000` adresine gidin.

## 🛠️ Teknolojiler

- **Backend:** Python, Flask, VSQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript
- **Veri İşleme:** Pandas, NumPy
- **Görüntü İşleme:** OpenCV, Tesseract OCR

