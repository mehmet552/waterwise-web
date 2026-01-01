# WaterWise Web

WaterWise Web, su tüketimini takip etmeyi, analiz etmeyi ve tasarruf sağlamayı amaçlayan bir web uygulamasıdır. Kullanıcıların su faturalarını analiz etmelerine, günlük hedefler belirlemelerine ve tüketim alışkanlıklarını görselleştirmelerine olanak tanır.

## Özellikler

- **Su Tüketimi Takibi:** Günlük aktiviteler (duş, bulaşık vb.) bazında su kullanımını kaydetme.
- **Fatura Analizi (OCR):** Su faturası fotoğraflarından otomatik tüketim verisi çıkarma ve doğrulama.
- **Görsel Raporlar:** Günlük, haftalık ve aylık tüketim grafikleri.
- **Topluluk ve Lider Tablosu:** Diğer kullanıcılarla tasarruf rekabeti.
- **Akıllı İpuçları:** Hava durumu ve kişisel kullanıma göre özel tasarruf önerileri.

## Kurulum

Projeyi yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyin.

### Gereksinimler

- Python 3.8+
- Tesseract OCR (Fatura analizi için gereklidir)
  - Windows için: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki) (Kurulum yolunu `app.py` içinde gerekirse güncelleyin, varsayılan: `C:\Program Files\Tesseract-OCR\tesseract.exe`)

### Adımlar

1.  Repoyu klonlayın veya indirin.
2.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
3.  `.env` dosyasını oluşturun:
    Proje ana dizininde `.env` adlı bir dosya oluşturun ve içine aşağıdaki bilgileri ekleyin (API anahtarlarınızı kendiniz belirleyin):
    ```env
    SECRET_KEY=gizli-bir-anahtar-belirleyin
    WEATHER_API_KEY=openweathermap_api_key_buraya
    ```
    *(Not: Weather API key için [OpenWeatherMap](https://openweathermap.org/) sitesinden ücretsiz key alabilirsiniz.)*

4.  Uygulamayı başlatın:
    ```bash
    python app.py
    ```
5.  Tarayıcınızda `http://127.0.0.1:5000` adresine gidin.

## Teknoloji Yığını

- **Backend:** Flask (Python)
- **Veritabanı:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **OCR:** Tesseract, OpenCV
- **Veri Analizi:** Pandas, NumPy

## Katkıda Bulunma

1.  Bu repoyu fork'layın.
2.  Yeni bir feature branch oluşturun (`git checkout -b yeni-ozellik`).
3.  Değişikliklerinizi commit'leyin (`git commit -m 'Yeni özellik eklendi'`).
4.  Branch'inizi push'layın (`git push origin yeni-ozellik`).
5.  Bir Pull Request (PR) oluşturun.
