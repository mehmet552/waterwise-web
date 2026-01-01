// === WaterWise Ana Script ===
// Sayfadaki tüm HTML yüklendiğinde çalışır
document.addEventListener('DOMContentLoaded', () => {

    // === Elemanlar ===
    const statusLabel = document.getElementById('status-label');
    const categorySelect = document.getElementById('category-select');
    const litersEntry = document.getElementById('liters-entry');
    const addButton = document.getElementById('add-button');
    const targetEntry = document.getElementById('target-entry');
    const targetButton = document.getElementById('target-button');
    const streakLabel = document.getElementById('streak-label');
    const summaryWeekLabel = document.getElementById('summary-week-label');
    const summaryCategoryLabel = document.getElementById('summary-category-label');
    const trendCtx = document.getElementById('dailyTrendChart')?.getContext('2d');
    const pieCtx = document.getElementById('categoryPieChart')?.getContext('2d');

    let trendChart, pieChart;

    // === Günlük Durum ===
    async function updateStatus() {
        try {
            const response = await fetch('/api/today_status');
            const data = await response.json();

            statusLabel.textContent = `Bugün: ${data.today_total.toFixed(1)} L / Hedef: ${data.daily_target.toFixed(1)} L`;

            const percentage = (data.today_total / data.daily_target) * 100;
            if (percentage > 100) {
                statusLabel.style.color = 'var(--status-bad)';
            } else if (percentage >= 90) {
                statusLabel.style.color = 'var(--status-warn)';
            } else {
                statusLabel.style.color = 'var(--status-good)';
            }

            targetEntry.value = data.daily_target.toFixed(1);
        } catch (error) {
            console.error('Durum güncellenirken hata:', error);
            statusLabel.textContent = 'Durum yüklenemedi.';
        }
    }

    // === Tasarruf Serisi ===
    async function updateStreak() {
        try {
            const response = await fetch('/api/streak');
            const data = await response.json();

            if (data.streak > 0) {
                streakLabel.textContent = `🔥 ${data.streak} Gündür Tasarruf Serisindesin!`;
                streakLabel.style.display = 'block';
            } else {
                streakLabel.style.display = 'none';
            }
        } catch (error) {
            console.error('Seri güncellenirken hata:', error);
        }
    }

    // === Haftalık Özet ===
    async function updateSummary() {
        try {
            const response = await fetch('/api/summary');
            const data = await response.json();
            // innerHTML kullanarak backend'den gelen <span> renklerini aktif ediyoruz
            summaryWeekLabel.innerHTML = data.week_comparison_text || "Veri bulunamadı.";
            summaryCategoryLabel.innerHTML = data.top_category_text || "";
        } catch (error) {
            console.error('Özet güncellenirken hata:', error);
            summaryWeekLabel.textContent = "Özet yüklenirken bir hata oluştu.";
        }
    }

    let currentPeriod = 'daily';

    // === Grafikler ===
    async function updateCharts() {
        try {
            const response = await fetch(`/api/report_data?period=${currentPeriod}`);
            const data = await response.json();

            // --- Günlük/Haftalık/Aylık Tüketim Grafiği ---
            let chartLabel = 'Günlük Tüketim (L)';
            if (currentPeriod === 'weekly') chartLabel = 'Haftalık Toplam (L)';
            if (currentPeriod === 'monthly') chartLabel = 'Aylık Toplam (L)';

            if (trendChart) trendChart.destroy();
            trendChart = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: data.daily_trend.labels,
                    datasets: [
                        {
                            label: chartLabel,
                            data: data.daily_trend.data,
                            borderColor: 'var(--primary-color)',
                            backgroundColor: 'var(--primary-color)',
                            tension: 0.1
                        },
                        {
                            label: `Hedef (${data.daily_trend.target} L)`,
                            data: Array(data.daily_trend.labels.length).fill(data.daily_trend.target),
                            borderColor: 'var(--status-bad)',
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { title: { display: true, text: chartLabel } }
                }
            });

            // --- Kategori Grafiği ---
            if (pieChart) pieChart.destroy();
            pieChart = new Chart(pieCtx, {
                type: 'pie',
                data: {
                    labels: data.category_pie.labels,
                    datasets: [{
                        data: data.category_pie.data,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                        ],
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { title: { display: true, text: 'Kategori Dağılımı' } }
                }
            });

            // --- Fatura Geçmişi Tablosu (YENİ) ---
            const billBody = document.getElementById('bill-history-body');
            if (billBody) {
                billBody.innerHTML = '';
                if (data.bill_history && data.bill_history.length > 0) {
                    data.bill_history.forEach(bill => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${bill.date}</td>
                            <td>${bill.amount_m3} m³</td>
                            <td>${bill.liters.toLocaleString()} L</td>
                            <td>
                                <button onclick="deleteConsumption(${bill.id})" class="btn btn-sm btn-danger" style="padding: 2px 8px; font-size: 0.8rem; background-color: #ef4444; color: white;">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </td>
                        `;
                        billBody.appendChild(row);
                    });
                } else {
                    billBody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#888;">Henüz fatura verisi yok.</td></tr>';
                }
            }

        } catch (error) {
            console.error('Grafikler güncellenirken hata:', error);
        }
    }

    // Global fonksiyon olarak dışarı açıyoruz (HTML'den erişilebilsin diye)
    window.changePeriod = function (period) {
        currentPeriod = period;
        // Buton stillerini güncelle
        document.querySelectorAll('.btn-period').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.period === period) btn.classList.add('active');
        });
        updateCharts();
    };

    // === Kategori Değişimi Dinleyicisi (YENİ) ===
    const amountLabel = document.getElementById('amount-label');
    const modelGroup = document.getElementById('model-selection-group');
    const modelSelect = document.getElementById('model-select');

    categorySelect.addEventListener('change', () => {
        const val = categorySelect.value;
        let labelText = "Miktar";

        // Reset Logic
        modelGroup.style.display = 'none';
        modelSelect.innerHTML = '';

        if (val === 'shower' || val === 'tap' || val === 'garden') {
            labelText = "Süre (Dakika)";
            litersEntry.placeholder = "Örn: 10";
        } else if (val === 'dishwasher' || val === 'washing_machine') {
            labelText = "Adet / Döngü";
            litersEntry.placeholder = "Örn: 1";

            // Show Model/Efficiency Selection
            modelGroup.style.display = 'block';
            if (val === 'dishwasher') {
                modelSelect.innerHTML = `
                    <option value="_eco">Eco Modu (~10L)</option>
                    <option value="_std" selected>Standart (~15L)</option>
                    <option value="_int">Yoğun Yıkama (~20L)</option>
                `;
            } else { // washing_machine
                modelSelect.innerHTML = `
                    <option value="_eco">Eco Modu (~35L)</option>
                    <option value="_std" selected>Standart (~50L)</option>
                    <option value="_int">Yoğun / Yorgan (~70L)</option>
                `;
            }

        } else if (val === 'car_wash') {
            labelText = "Yıkama Sayısı";
            litersEntry.placeholder = "Örn: 1";
        } else {
            labelText = "Miktar (Litre)";
            litersEntry.placeholder = "Örn: 10.5";
        }
        amountLabel.textContent = labelText;
    });

    // === Tüketim Ekle (GÜNCELLENDİ) ===
    addButton.addEventListener('click', async () => {
        let activity = categorySelect.value;
        const amount = parseFloat(litersEntry.value);

        // Eğer makine seçiliyse, mod ekle
        if (modelGroup.style.display !== 'none') {
            activity += modelSelect.value; // örn: dishwasher + _eco -> dishwasher_eco
        }

        if (!amount || isNaN(amount) || amount <= 0) {
            Swal.fire('Uyarı', "Lütfen geçerli bir değer girin.", 'warning');
            return;
        }

        addButton.disabled = true;
        addButton.textContent = "Kaydediliyor...";

        try {
            // YENİ API PAYLOAD YAPISI
            const payload = {
                activity: activity,
                amount: amount
            };

            const response = await fetch('/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.success) {
                litersEntry.value = '';
                alert(`✅ ${result.message}`); // Kullanıcıya hesaplanan litreyi göster
                updateStatus();
                updateCharts();
                updateStreak();
                updateSummary();
            } else {
                alert("Veri eklenirken hata: " + (result.message || "Bilinmeyen hata."));
            }
        } catch (error) {
            console.error('Ekleme hatası:', error);
        } finally {
            addButton.disabled = false;
            addButton.textContent = "Kaydet";
        }
    });

    // === Hedef Güncelle ===
    targetButton.addEventListener('click', async () => {
        const target = parseFloat(targetEntry.value);
        if (!target || isNaN(target) || target <= 0) {
            alert("Lütfen geçerli bir hedef girin.");
            return;
        }

        targetButton.disabled = true;
        targetButton.textContent = "Güncelleniyor...";

        try {
            const response = await fetch('/api/target', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target })
            });
            const result = await response.json();

            if (result.success) {
                alert("Hedef güncellendi!");
                updateStatus();
                updateCharts();
                updateStreak();
                updateSummary();
            } else {
                alert("Hedef güncellenirken hata: " + (result.message || "Bilinmeyen hata."));
            }
        } catch (error) {
            console.error('Hedef güncelleme hatası:', error);
        } finally {
            targetButton.disabled = false;
            targetButton.textContent = "Hedefi Güncelle";
        }
    });

    // === Bugünü Sıfırla (YENİ) ===
    const resetButton = document.getElementById('reset-button');
    if (resetButton) {
        resetButton.addEventListener('click', async () => {
            const confirmResult = await Swal.fire({
                title: 'Emin misiniz?',
                text: "Bugüne ait tüm su tüketim verileri silinecek!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Evet, Sıfırla',
                cancelButtonText: 'İptal'
            });

            if (confirmResult.isConfirmed) {
                try {
                    const response = await fetch('/api/reset_today', { method: 'POST' });
                    const result = await response.json();

                    if (result.success) {
                        Swal.fire('Sıfırlandı!', result.message, 'success');
                        updateStatus();
                        updateCharts();
                        updateStreak();
                        updateSummary();
                    } else {
                        Swal.fire('Hata', result.message, 'error');
                    }
                } catch (error) {
                    console.error('Sıfırlama hatası:', error);
                    Swal.fire('Hata', 'Bağlantı sorunu.', 'error');
                }
            }
        });
    }

    // === Sayfa ilk açıldığında verileri yükle ===
    updateStatus();
    updateCharts();
    updateStreak();
    updateSummary();

    // === Silme Fonksiyonu (Scope içine taşındı) ===
    window.deleteConsumption = async function (id) {
        const confirmResult = await Swal.fire({
            title: 'Emin misiniz?',
            text: "Bu fatura kaydı kalıcı olarak silinecek!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Evet, Sil',
            cancelButtonText: 'İptal'
        });

        if (confirmResult.isConfirmed) {
            try {
                const response = await fetch(`/api/delete_consumption/${id}`, { method: 'DELETE' });
                const result = await response.json();

                if (result.success) {
                    Swal.fire('Silindi!', result.message, 'success');
                    // Tabloyu güncelle
                    updateCharts();
                    updateStatus();
                    updateSummary();
                } else {
                    Swal.fire('Hata', result.message, 'error');
                }
            } catch (error) {
                console.error('Silme hatası:', error);
                Swal.fire('Hata', 'Bağlantı sorunu.', 'error');
            }
        }
    };

});


// === Hava Durumu ve Öneri ===
if (document.getElementById('weather-info')) {
    fetch('/weather-advice')
        .then(response => response.json())
        .then(data => {
            const weatherBox = document.getElementById('weather-info');
            if (data.error) {
                weatherBox.innerHTML = 'Hava durumu bilgisi alınamadı.';
                return;
            }

            const city = (data.city || '').replace(/\s+/g, ' ').trim();
            const temp = (data.temp || '').toString().trim();
            const advice = (data.advice || '').trim();

            // Görsel ikon ekleme (isteğe bağlı)
            const iconUrl = data.icon ?
                `https://openweathermap.org/img/wn/${data.icon}@2x.png` : '';

            weatherBox.innerHTML = `
        ${iconUrl ? `<img src="${iconUrl}" alt="hava" style="width:45px;vertical-align:middle;">` : ''}
        <strong>${city}</strong> • ${temp}°C<br>
        <em>${advice}</em>
      `;
        })
        .catch(() => {
            document.getElementById('weather-info').innerHTML = 'Hava durumu bilgisi alınamadı.';
        });
}


// === Günlük Hatırlatma ===
(function () {
    try {
        const today = new Date().toLocaleDateString();
        if (localStorage.getItem('lastReminder') !== today) {
            if (confirm('💧 Bugün su tüketimini kaydetmeyi unutma! Kaydetmek ister misin?')) {
                const input = document.getElementById('liters-entry');
                if (input) input.focus();
            }
            localStorage.setItem('lastReminder', today);
        }
    } catch (e) { console.warn('Hatırlatma hatası:', e); }
})();

// === Fatura Tutarından Tüketim Bul (Ters Hesap) ===
window.calculateUsageFromPrice = async function () {
    const price = document.getElementById('calc-price').value;
    const type = document.getElementById('calc-type-rev').value;

    if (!price || price <= 0) {
        Swal.fire('Hata', "Lütfen geçerli bir fatura tutarı girin.", 'error');
        return;
    }

    try {
        const response = await fetch('/api/estimate_usage_from_price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ price: price, user_type: type })
        });

        const res = await response.json();
        if (res.success) {
            document.getElementById('rev-usage').textContent = res.usage_m3 + " m³";
            document.getElementById('rev-liters').textContent = Math.round(res.liters).toLocaleString() + " Litre";
            document.getElementById('rev-result').style.display = 'block';

            // Global değişkene ata (ekleme işlemi için)
            window.calculatedLiters = res.liters;
        }
    } catch (e) {
        console.error(e);
        Swal.fire('Hata', "Hesaplama hatası.", 'error');
    }
};

window.addCalculatedUsage = async function () {
    if (!window.calculatedLiters) return;

    // Doğrudan Custom/Diğer olarak ekle
    try {
        const payload = {
            activity: 'bill',
            amount: window.calculatedLiters
        };

        const response = await fetch('/api/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
            Swal.fire('Başarılı', `Toplam ${Math.round(window.calculatedLiters)} Litre tüketim eklendi!`, 'success');
            // Dashboard güncelle
            document.getElementById('status-label').textContent = "Güncelleniyor..."; // Hızlı görsel geri bildirim
            setTimeout(() => location.reload(), 1500); // En temiz güncelleme reload olabilir veya fonksiyonları çağırırız
        } else {
            Swal.fire('Hata', result.message, 'error');
        }
    } catch (e) {
        console.error(e);
    }
};


