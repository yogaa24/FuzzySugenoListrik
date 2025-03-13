from flask import Flask, render_template, request, redirect, url_for, Response
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time
from datetime import datetime
import pandas as pd
import os
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inisialisasi Firebase
try:
    cred = credentials.Certificate("./monitoring.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase berhasil diinisialisasi")
except Exception as e:
    logger.error(f"Gagal menginisialisasi Firebase: {str(e)}")

# Fungsi fuzzy yang disederhanakan
def fuzzyLogic(Power, jumlahperangkat=1, HasilDaya=0, stopwatch=0, biayalistrik=0):
    # Input Fuzzy
    daya_listrik = float(Power)
    Sum_perangkat = float(jumlahperangkat)
    Daya = float(HasilDaya)
    waktu = float(stopwatch)
    biaya = float(biayalistrik)
    
    # Fungsi keanggotaan untuk Power (daya listrik)
    def membership_power(x):
        power_rendah = 0
        power_sedang = 0
        power_tinggi = 0
        
        # Rendah
        if x < 0.66:
            power_rendah = 1
        elif x < 1:
            power_rendah = (1 - x)/(1 - 0.83)
        
        # Sedang
        if 0.83 <= x < 1.66:
            power_sedang = (x - 0.83)/(1.6 - 0.83)
        elif 1.66 <= x < 2.5:
            power_sedang = (2.5 - x)/(2.5 - 1.6)
        
        # Tinggi
        if 2.33 <= x < 3.66:
            power_tinggi = (x - 3.66)/(3.66 - 2.33)
        elif x >= 3.66:
            power_tinggi = 1
            
        return [power_rendah, power_sedang, power_tinggi]
    
    # Fungsi keanggotaan untuk jumlah perangkat
    def membership_jumlah(x):
        jumlah_sedikit = 0
        jumlah_sedang = 0
        jumlah_banyak = 0
        
        # Sedikit
        if x < 2:
            jumlah_sedikit = 1
        elif x < 4:
            jumlah_sedikit = (4 - x)/(4 - 2)
            
        # Sedang
        if 2 <= x < 4:
            jumlah_sedang = (x - 2)/(4 - 2)
        elif 4 <= x < 6:
            jumlah_sedang = 1
        elif 6 <= x < 8:
            jumlah_sedang = (8 - x)/(8 - 6)
            
        # Banyak
        if 6 <= x < 8:
            jumlah_banyak = (x - 6)/(8 - 6)
        elif x >= 8:
            jumlah_banyak = 1
            
        return [jumlah_sedikit, jumlah_sedang, jumlah_banyak]
    
    # Fungsi keanggotaan untuk hasil daya
    def membership_hasildaya(x):
        daya_rendah = 0
        daya_normal = 0
        daya_tinggi = 0
        
        # Rendah
        if x < 400:
            daya_rendah = 1
        elif x < 900:
            daya_rendah = (900 - x)/(900 - 400)
            
        # Normal
        if 400 <= x < 900:
            daya_normal = (x - 400)/(900 - 400)
        elif 900 <= x < 1400:
            daya_normal = (1400 - x)/(1400 - 900)
            
        # Tinggi
        if 900 <= x < 1400:
            daya_tinggi = (x - 900)/(1400 - 900)
        elif x >= 1400:
            daya_tinggi = 1
            
        return [daya_rendah, daya_normal, daya_tinggi]
    
    # Fungsi keanggotaan untuk waktu
    def membership_waktu(x):
        waktu_cepat = 0
        waktu_normal = 0
        waktu_lama = 0
        
        # Cepat
        if x < 6:
            waktu_cepat = 1
        elif x < 8:
            waktu_cepat = (8 - x)/(8 - 6)
            
        # Normal
        if 6 <= x < 8:
            waktu_normal = (x - 6)/(8 - 6)
        elif 8 <= x < 10:
            waktu_normal = 1
        elif 10 <= x < 12:
            waktu_normal = (12 - x)/(12 - 10)
            
        # Lama
        if 10 <= x < 12:
            waktu_lama = (x - 10)/(12 - 10)
        elif x >= 12:
            waktu_lama = 1
            
        return [waktu_cepat, waktu_normal, waktu_lama]
    
    # Fungsi keanggotaan untuk biaya listrik
    def membership_biaya(x):
        biaya_murah = 0
        biaya_mahal = 0
        
        # Murah
        if x < 4000:
            biaya_murah = 1
        elif x < 7000:
            biaya_murah = (7000 - x)/(7000 - 4000)
            
        # Mahal
        if 4000 <= x < 7000:
            biaya_mahal = (x - 4000)/(7000 - 4000)
        elif x >= 7000:
            biaya_mahal = 1
            
        return [biaya_murah, biaya_mahal]
    
    # Hitung membership untuk setiap input
    Power = membership_power(daya_listrik)
    jumlahperangkat = membership_jumlah(Sum_perangkat)
    HasilDaya = membership_hasildaya(Daya)
    stopwatch = membership_waktu(waktu)
    biayalistrik = membership_biaya(biaya)
    
    # Kategori output
    penggunaan_Rendah = 0
    penggunaan_normal = 1
    penggunaan_tinggi = 2
    
    # Perhitungan inferensi menggunakan metode Mamdani
    rules_fired = []
    for i in range(3):  # Power
        for j in range(3):  # Waktu
            for k in range(3):  # HasilDaya
                for l in range(3):  # JumlahPerangkat
                    for m in range(2):  # BiayaListrik
                        # Aplikasi min untuk mendapatkan nilai alpha-cut
                        alpha = min(Power[i], stopwatch[j], HasilDaya[k], jumlahperangkat[l], biayalistrik[m])
                        
                        # Tentukan konsekuensi berdasarkan aturan
                        # Logika aturan sederhana:
                        # Jika power tinggi atau waktu lama, maka penggunaan tinggi
                        # Jika power sedang dan waktu normal, maka penggunaan normal
                        # Selain itu, penggunaan rendah
                        if i == 2 and j == 2:  # Power tinggi dan waktu lama
                            output = penggunaan_tinggi
                        elif i == 1 and j == 1:  # Power sedang dan waktu normal
                            output = penggunaan_normal
                        else:
                            output = penggunaan_Rendah
                        
                        # Tambahkan ke daftar rules yang fired
                        if alpha > 0:
                            rules_fired.append((alpha, output))
    
    # Kalkulasi defuzzifikasi centroid sederhana
    if not rules_fired:
        return {"fuzy": 0, "text": "Penggunaan Rendah"}
    
    numerator = sum(alpha * output for alpha, output in rules_fired)
    denominator = sum(alpha for alpha, output in rules_fired)
    
    if denominator == 0:
        z = 0
    else:
        z = numerator / denominator
    
    # Interpretasi hasil
    if z <= 0.67:
        return {"fuzy": round(z, 2), "text": "Penggunaan Rendah"}
    elif z <= 1.33:
        return {"fuzy": round(z, 2), "text": "Penggunaan Sedang"}
    else:
        return {"fuzy": round(z, 2), "text": "Penggunaan Tinggi"}

# Fungsi untuk membuat response JSON
def response(code, msg, data):
    return Response(
        status=code,
        response=json.dumps({
            "status": code == 200,
            "code": code,
            "msg": msg,
            "data": data
        }),
        mimetype='application/json',
        headers={'Access-Control-Allow-Origin': '*'}
    )

# Fungsi untuk menghitung biaya listrik
def biaya(daya, total):
    if daya <= 900:
        return total * 1352
    elif daya <= 1300 or daya <= 2200:
        return total * 1452
    elif daya <= 3500 or daya <= 5500:
        return total * 1699
    return total * 1699  # Default untuk daya > 5500

# Fungsi untuk format rupiah
def formatRupiah(angka):
    rupiah = ''
    angka = str(angka)
    panjang = len(angka)
    while panjang > 3:
        rupiah = '.' + angka[-3:] + rupiah
        angka = angka[:-3]
        panjang = len(angka)
    rupiah = angka + rupiah
    return rupiah

# Fungsi untuk mendapatkan data dari Firestore dengan lazy loading
def getData(arrayWaktu, daya):
    try:
        dataFuzy = []
        resultTable = []
        energyTotal = 0
        hargaTotal = 0
        
        if len(arrayWaktu) <= 0:
            logger.warning("Tidak ada tanggal yang diberikan untuk query")
            return response(400, "Bad Request", data=None)

        for i in range(len(arrayWaktu)):
            try:
                dt = datetime.strptime(arrayWaktu[i], "%Y-%m-%d")
                dts = datetime.replace(dt, hour=23, minute=58, second=59, microsecond=0)
                
                # Query Firestore
                getLastestDataFromFirestore = db.collection('DataBase3Jalur').where(
                    'TimeStamp', ">=", dts).limit(1).get()

                if len(getLastestDataFromFirestore) == 0:
                    logger.info(f"Tidak ada data untuk tanggal {arrayWaktu[i]}")
                    continue

                dataTerakhir = getLastestDataFromFirestore[0].to_dict()
                timeElapse = dataTerakhir['TimeStamp'].replace(tzinfo=None) - dt.replace(tzinfo=None)
                stopwatch = round(timeElapse.total_seconds() / 3600)
                
                # Ambil nilai energytotal
                energyTerakhir = 0.00
                if 'energytotal' in dataTerakhir:
                    energyTerakhir = dataTerakhir['energytotal']
                elif 'energyTotal' in dataTerakhir:
                    energyTerakhir = dataTerakhir['energyTotal']
                
                # Ambil jumlah perangkat
                dataPerangkat = dataTerakhir.get('JumlahPerangkat', 0)
                
                # Hitung fuzzy
                fuzzy_result = fuzzyLogic(
                    energyTerakhir,
                    3,  # Default jumlah perangkat
                    daya,
                    stopwatch,
                    dataTerakhir.get('HargaListrik', 0)
                )
                
                # Format tanggal
                formatted_date = dt.strftime("%d - %m - %Y")
                formatted_date_long = dt.strftime("%d %B %Y")
                
                # Tambahkan ke hasil
                dataFuzy.append({
                    "waktu": formatted_date,
                    "dataFuzy": fuzzy_result,
                })
                
                # Hitung biaya
                biaya_listrik = biaya(daya, energyTerakhir)
                
                resultTable.append({
                    "waktu": formatted_date_long,
                    "power": dataPerangkat,
                    "energy": energyTerakhir,
                    "biaya": "Rp. " + formatRupiah(round(biaya_listrik)),
                    "stopwatch": stopwatch,
                    "jumlah": dataTerakhir.get('JumlahPerangkat', 0)
                })
                
                # Update total
                energyTotal += energyTerakhir
                hargaTotal += biaya_listrik
                
            except Exception as e:
                logger.error(f"Error memproses data tanggal {arrayWaktu[i]}: {str(e)}")
                continue

        return {
            "dataFuzy": dataFuzy,
            "resultTable": resultTable,
            "energyTotal": round(energyTotal, 3),
            "hargaTotal": "Rp. " + formatRupiah(round(hargaTotal))
        }
        
    except Exception as e:
        logger.error(f"Error dalam getData: {str(e)}")
        return None

# Inisialisasi Flask
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return response(200, "OK", "Hello World")

@app.route('/fuzzy', methods=['POST'])
def fuzzys():
    try:
        # Validasi input
        required_fields = ['start_date', 'end_date', 'daya']
        if not all(field in request.json for field in required_fields):
            logger.warning(f"Missing fields in request: {request.json}")
            return response(400, "Bad Request - Missing Fields", data=None)

        start_date = request.json['start_date']
        end_date = request.json['end_date']
        daya = request.json['daya']
        
        logger.info(f"Request: start_date={start_date}, end_date={end_date}, daya={daya}")

        # Generate range tanggal
        dtrange = pd.date_range(start=start_date, end=end_date, freq='d')
        arrayWaktu = [dt.strftime("%Y-%m-%d") for dt in dtrange]
        
        # Proses data
        data = getData(arrayWaktu, daya)
        if data is None:
            return response(500, "Internal Server Error", data=None)
            
        logger.info("Data berhasil diproses")
        return response(200, "OK", data=data)
        
    except Exception as e:
        logger.error(f"Error dalam endpoint fuzzy: {str(e)}")
        return response(500, "Internal Server Error", data=None)

if __name__ == "__main__":
    logger.info("Server is running on port 5000")
    port = int(os.getenv('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)