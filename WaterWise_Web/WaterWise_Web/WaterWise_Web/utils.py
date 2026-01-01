
def calculate_water_usage(activity_type, amount):
    """
    Seçilen aktiviteye ve miktara göre su tüketimini (Litre) hesaplar.
    
    Args:
        activity_type (str): Aktivite türü
        amount (float): Aktivite süresi (dk) veya döngü sayısı
        
    Returns:
        float: Hesaplanan su miktarı (Litre)
    """
    
    # Standart Katsayılar (Litre)
    RATES = {
        'shower': 12,            # 12 Litre / Dakika
        'tap': 6,                # 6 Litre / Dakika
        'dishwasher': 15,        # Standart (Eski veri uyumluluğu için)
        'dishwasher_eco': 10,    # Eco Program
        'dishwasher_std': 15,    # Standart
        'dishwasher_int': 20,    # Yoğun
        'washing_machine': 50,   # Standart
        'washing_machine_eco': 35, # Eco
        'washing_machine_std': 50, # Standart
        'washing_machine_int': 70, # Yoğun (Yorgan vb)
        'garden': 20,            # 20 Litre / Dakika
        'car_wash': 100,         # 100-200 arası değişir, ortalama
        'bucket': 10,
        'bill': 1, # Fatura (m3 -> Litre çevirimi dışarıda yapılıyor veya 1 kabul ediliyor)
        'custom': 1
    }
    
    rate = RATES.get(activity_type, 1)
    
    if activity_type not in RATES and activity_type != 'custom':
        return amount
        
    return amount * rate

def get_activity_label(activity_type):
    """Aktivite kodunun anlaşılır ismini döndürür."""
    LABELS = {
        'shower': 'Duş',
        'tap': 'Musluk Kullanımı',
        'dishwasher': 'Bulaşık Makinesi',
        'washing_machine': 'Çamaşır Makinesi',
        'garden': 'Bahçe Sulama',
        'car_wash': 'Araç Yıkama',
        'bill': 'Fatura Bildirimi',
        'custom': 'Diğer (Manuel)'
    }
    return LABELS.get(activity_type, activity_type.capitalize())

def calculate_iski_bill(usage_m3, user_type='residential', manual_rates=None):
    """
    ISKI 2025 Tarifesine göre fatura hesaplar.
    """
    import math

    # Varsayılan Tarifeler (2025)
    # Tier 1: 0-15 m3, Tier 2: 16-30 m3, Tier 3: 31+ m3
    RATES = {
        'water_tier1': 34.67,
        'water_tier2': 52.83,
        'water_tier3': 76.41,
        'waste_tier1': 17.335,
        'waste_tier2': 26.415,
        'waste_tier3': 38.205,
        'ctv_rate': 0.015, # ÇTV m3 başına (1.5 kuruş = 0.015 TL)
        'kdv_rate': 0.08   # %8 KDV
    }
    
    # Manuel fiyatlar varsa güncelle
    if manual_rates:
        # manual_rates anahtarları RATES ile eşleşmelidir
        RATES.update(manual_rates)

    usage = float(usage_m3)
    
    # 1. İnsani Su Hakkı İndirimi
    # "2.5 m3 tüketimde 0.5 m3 bedava" -> İlk 15 m3 için geçerli
    eligible_for_deduction = min(usage, 15.0)
    deduction_blocks = math.floor(eligible_for_deduction / 2.5)
    deduction_m3 = deduction_blocks * 0.5
    
    billable_usage = usage 
    
    # Kademe Hesaplama
    cost_water = 0.0
    cost_waste = 0.0
    
    # Tier 1 (0-15)
    tier1_amount = min(billable_usage, 15.0)
    
    # Tier 1'den indirimli miktarı düş (Parasal olarak)
    payable_tier1 = max(0, tier1_amount - deduction_m3)
    
    cost_water += payable_tier1 * RATES['water_tier1']
    cost_waste += payable_tier1 * RATES['waste_tier1']
    
    remaining = billable_usage - 15.0
    
    # Tier 2 (16-30)
    if remaining > 0:
        tier2_amount = min(remaining, 15.0)
        cost_water += tier2_amount * RATES['water_tier2']
        cost_waste += tier2_amount * RATES['waste_tier2']
        remaining -= 15.0
        
    # Tier 3 (30+)
    if remaining > 0:
        cost_water += remaining * RATES['water_tier3']
        cost_waste += remaining * RATES['waste_tier3']
        
    # İndirim Grubu Kontrolü (%50)
    discount_rate = 0.0
    if user_type in ['student', 'disabled', 'martyr']:
        discount_rate = 0.50
        cost_water *= (1 - discount_rate)
        cost_waste *= (1 - discount_rate)
    
    # Vergiler
    billed_volume = max(0, usage - deduction_m3)
    ctv_total = billed_volume * RATES['ctv_rate']
    
    subtotal = cost_water + cost_waste
    kdv_total = subtotal * RATES['kdv_rate']
    
    total_bill = subtotal + ctv_total + kdv_total
    
    return {
        'usage_m3': usage,
        'deduction_m3': deduction_m3,
        'billed_m3': billed_volume,
        'water_cost': round(cost_water, 2),
        'waste_cost': round(cost_waste, 2),
        'ctv': round(ctv_total, 2),
        'kdv': round(kdv_total, 2),
        'total': round(total_bill, 2),
        'currency': 'TL'
    }

def solve_usage_from_price(target_price_tl, user_type='residential'):
    """
    Verilen fatura tutarına (TL) denk gelen kullanımı (m3) hesaplar.
    Binary Search kullanır.
    """
    target = float(target_price_tl)
    low = 0.0
    high = 500.0 # Bireysel kullanıcı için mantıklı üst sınır (500m3 devasa bir rakam)
    tolerance = 0.5 # 0.5 TL fark kabul edilebilir
    
    found_m3 = 0
    
    # 50 iterasyon yeterli hassasiyet sağlar
    for _ in range(50):
        mid = (low + high) / 2
        res = calculate_iski_bill(mid, user_type)
        mid_price = res['total']
        
        if abs(mid_price - target) < tolerance:
            found_m3 = mid
            break
        
        if mid_price < target:
            low = mid
        else:
            high = mid
            
    return round(found_m3, 2)
