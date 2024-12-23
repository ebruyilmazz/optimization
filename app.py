from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

# depo verileri
data_path = "data/depo_verileri.json"

# JSON'dan depo verilerini yükleme
def load_data():
    try:
        with open(data_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Hata: {data_path} dosyası bulunamadı.")
        return {}
    except json.JSONDecodeError:
        print(f"Hata: {data_path} dosyasında geçerli JSON formatı bulunamadı.")
        return {}

# JSON'a depo verilerini kaydetme
def save_data(data):
    try:
        with open(data_path, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Veri kaydetme hatası: {e}")

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', depolar=data.get('depolar', []))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    data = load_data()
    if request.method == 'POST':
        for i, depo in enumerate(data['depolar']):
            depo['stok'] = int(request.form[f'stok_{i}'])
            depo['arac_sayisi'] = int(request.form[f'arac_sayisi_{i}'])
            depo['max_uzaklik'] = int(request.form[f'max_uzaklik_{i}'])
            depo['tasima_maliyeti'] = float(request.form[f'tasima_maliyeti_{i}'])
        save_data(data)
        return redirect(url_for('admin'))
    return render_template('admin.html', depolar=data.get('depolar', []))

@app.route('/user', methods=['GET', 'POST'])
def user():
    data = load_data()
    if request.method == 'POST':
        stok_talepleri = {
            f'magaza_{i}': {
                'toplam_stok': int(request.form[f'stok_talebi_{i}']),
                'uzakliklar': [int(request.form[f'uzaklik_{i}_{j}']) for j in range(3)]
            }
            for i in range(4)
        }
        data['stok_talepleri'] = stok_talepleri
        save_data(data)
        return redirect(url_for('results'))
    return render_template('user.html')

@app.route('/results')
def results():
    data = load_data()
    depolar = data.get('depolar', [])
    talepler = data.get('stok_talepleri', {})

    results = {
        'detaylar': [],
        'grafik': {'labels': [], 'values': []},
        'toplam_maliyet': 0,
        'durum': '',
        'hatalar': [],  # Hatalı girişler için uyarı listesi
        'stok_yetersiz': [],  # Yetersiz stok uyarıları için liste
        
    }

    toplam_maliyet = 0
    toplam_depo_stok = sum([depo['stok'] for depo in depolar])
    toplam_talep = sum([talep['toplam_stok'] for talep in talepler.values()])

    # Her depo için araçları ve malları belirleme
    arac_kullanim = {depo['ad']: 0 for depo in depolar}  # Depo başına araç kullanımı

    for magaza, talep in talepler.items():
        magaza_adi = f"Mağaza {int(magaza.split('_')[1]) + 1}"
        en_uygun_depo = None
        en_dusuk_maliyet = float('inf')
        hatali_giris = False

        toplam_stok_gonderildi = 0  # Mağazaya gönderilen toplam stok miktarı

        for i, depo in enumerate(depolar):
            # Mağaza uzaklığı depo aracının max_uzaklik değerini aşarsa hata mesajı ekle
            if any(talep['uzakliklar'][i] > depo['max_uzaklik'] for i in range(len(talep['uzakliklar']))):
                results['hatalar'].append(f"{magaza_adi} için girilen uzaklık depo araçlarının ulaşabileceği mesafeyi aşıyor.")
                hatali_giris = True
                break  # Hatalı giriş varsa, bu mağazaya ait maliyet hesaplanmasın

            # Depo aracı yalnızca bir mağaza için kullanılabilir
            if arac_kullanim[depo['ad']] < depo['arac_sayisi'] and not hatali_giris:
                stok_gonderilecek = min(talep['toplam_stok'], depo['stok'])
                toplam_stok_gonderildi += stok_gonderilecek  # Gönderilen stok miktarını artır

                maliyet = stok_gonderilecek * depo['tasima_maliyeti'] * talep['uzakliklar'][i]

                if maliyet < en_dusuk_maliyet:
                    en_dusuk_maliyet = maliyet
                    en_uygun_depo = depo['ad']

        # Eğer talep edilen toplam stok, gönderilen stoktan fazlaysa yetersiz stok uyarısı ekle
        if toplam_stok_gonderildi < talep['toplam_stok']:
            results['stok_yetersiz'].append(f"{magaza_adi} için yeterli ürün yok. Talep edilen miktarın tamamı gönderilemedi.")
            hatali_giris=True
            continue

        # Eğer hata yoksa ve uygun depo bulunmuşsa işlemi tamamla
        if not hatali_giris and en_uygun_depo:
            arac_kullanim[en_uygun_depo] += 1  # Depo aracını kullandık

            results['detaylar'].append({
                'depo': en_uygun_depo,
                'magaza': magaza_adi,
                'urun': talep['toplam_stok'],
                'maliyet': en_dusuk_maliyet
            })
            toplam_maliyet += en_dusuk_maliyet

            # Grafik verilerini eklemeden önce tür kontrolü yap
            if isinstance(magaza_adi, str) and isinstance(en_dusuk_maliyet, (int, float)):
                results['grafik']['labels'].append(magaza_adi)
                results['grafik']['values'].append(en_dusuk_maliyet)

    # Toplam maliyet ekleme
    results['toplam_maliyet'] = toplam_maliyet

    # Optimal durum kontrolü
    if toplam_depo_stok >= toplam_talep:
        results['durum'] = "Optimal"
    else:
        results['durum'] = "Optimal Değil"

    # Verileri render etmeye gönder
    return render_template('results.html', results=results)



if __name__ == '__main__':
    app.run(debug=True)
