from flask import Flask, render_template, request, redirect, url_for, Response
import json
from datetime import datetime
from flask_cors import CORS
import pandas as pd
import os
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
import pytz
from google.cloud.firestore_v1.base_query import FieldFilter

# --------------------------
# Inisialisasi Firestore
# --------------------------

# Buat file kredensial sementara jika variabel FIREBASE_CREDENTIALS tersedia
if 'FIREBASE_CREDENTIALS' in os.environ:
    cred_json = os.environ['FIREBASE_CREDENTIALS']
    cred_dict = json.loads(cred_json)

    # Simpan ke file sementara
    temp_path = "/tmp/firebase_credentials.json"
    with open(temp_path, "w") as f:
        json.dump(cred_dict, f)

    # Set environment agar Google Cloud SDK bisa menggunakannya
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path



def fuzzyLogic(Power, jumlahperangkat=1, HasilDaya=0, stopwatch=0, biayalistrik=0):
    # Input values
    daya_listrik = float(Power)
    Sum_perangkat = float(jumlahperangkat)
    Daya = float(HasilDaya)
    waktu = float(stopwatch)
    biaya = float(biayalistrik)
    
    # Initialize membership arrays
    Power = [0, 0, 0]        # [Rendah, Sedang, Tinggi]
    jumlahperangkat = [0, 0, 0]  # [Sedikit, Sedang, Banyak]
    HasilDaya = [0, 0, 0]    # [Rendah, Normal, Tinggi]
    stopwatch = [0, 0, 0]    # [Cepat, Normal, Lama]
    biayalistrik = [0, 0]    # [Normal, Mahal]
    
    # Constants for defuzzification
    penggunaan_Rendah = 0
    penggunaan_normal = 1
    penggunaan_tinggi = 2
    
    # Fuzzification
    
    # KwH Membership Functions
    # KwH Rendah: [0, 0.66, 0.83]
    if daya_listrik <= 0.66:
        Power[0] = 1
    elif 0.66 < daya_listrik < 0.83:
        Power[0] = (0.83 - daya_listrik) / (0.83 - 0.66)
    else:
        Power[0] = 0
        
    # KwH Sedang: [0.66, 0.833, 1.66, 2.5]
    if daya_listrik <= 0.66 or daya_listrik >= 2.5:
        Power[1] = 0
    elif 0.66 < daya_listrik <= 0.833:
        Power[1] = (daya_listrik - 0.66) / (0.833 - 0.66)
    elif 0.833 < daya_listrik <= 1.66:
        Power[1] = 1
    elif 1.66 < daya_listrik < 2.5:
        Power[1] = (2.5 - daya_listrik) / (2.5 - 1.66)
    else:
        Power[1] = 0
        
    # KwH Tinggi: [1.66, 2.5, 4]
    if daya_listrik <= 1.66:
        Power[2] = 0
    elif 1.66 < daya_listrik < 2.5:
        Power[2] = (daya_listrik - 1.66) / (2.5 - 1.66)
    else:
        Power[2] = 1
    
    # Jumlah Perangkat Membership Functions
    # Perangkat Sedikit: [0, 2, 4]
    if Sum_perangkat <= 2:
        jumlahperangkat[0] = 1
    elif 2 < Sum_perangkat < 4:
        jumlahperangkat[0] = (4 - Sum_perangkat) / (4 - 2)
    else:
        jumlahperangkat[0] = 0
        
    # Perangkat Sedang: [2, 4, 6, 8]
    if Sum_perangkat <= 2 or Sum_perangkat >= 8:
        jumlahperangkat[1] = 0
    elif 2 < Sum_perangkat <= 4:
        jumlahperangkat[1] = (Sum_perangkat - 2) / (4 - 2)
    elif 4 < Sum_perangkat <= 6:
        jumlahperangkat[1] = 1
    elif 6 < Sum_perangkat < 8:
        jumlahperangkat[1] = (8 - Sum_perangkat) / (8 - 6)
    else:
        jumlahperangkat[1] = 0
        
    # Perangkat Banyak: [6, 8, 10]
    if Sum_perangkat <= 6:
        jumlahperangkat[2] = 0
    elif 6 < Sum_perangkat < 8:
        jumlahperangkat[2] = (Sum_perangkat - 6) / (8 - 6)
    else:
        jumlahperangkat[2] = 1
    
    # Daya Listrik Membership Functions
    # Daya Rendah: [0, 900, 1300]
    if Daya <= 900:
        HasilDaya[0] = 1
    elif 900 < Daya < 1300:
        HasilDaya[0] = (1300 - Daya) / (1300 - 900)
    else:
        HasilDaya[0] = 0
        
    # Daya Normal: [900, 1300, 2200]
    if Daya <= 900 or Daya >= 2200:
        HasilDaya[1] = 0
    elif 900 < Daya <= 1300:
        HasilDaya[1] = (Daya - 900) / (1300 - 900)
    elif 1300 < Daya < 2200:
        HasilDaya[1] = (2200 - Daya) / (2200 - 1300)
    else:
        HasilDaya[1] = 0
        
    # Daya Tinggi: [1300, 2200, 3000]
    if Daya <= 1300:
        HasilDaya[2] = 0
    elif 1300 < Daya < 2200:
        HasilDaya[2] = (Daya - 1300) / (2200 - 1300)
    else:
        HasilDaya[2] = 1
    
    # Waktu Membership Functions
    # Waktu Cepat: [0, 6, 8]
    if waktu <= 6:
        stopwatch[0] = 1
    elif 6 < waktu < 8:
        stopwatch[0] = (8 - waktu) / (8 - 6)
    else:
        stopwatch[0] = 0
        
    # Waktu Normal: [6, 8, 10, 12]
    if waktu <= 6 or waktu >= 12:
        stopwatch[1] = 0
    elif 6 < waktu <= 8:
        stopwatch[1] = (waktu - 6) / (8 - 6)
    elif 8 < waktu <= 10:
        stopwatch[1] = 1
    elif 10 < waktu < 12:
        stopwatch[1] = (12 - waktu) / (12 - 10)
    else:
        stopwatch[1] = 0
        
    # Waktu Lama: [10, 12, 24]
    if waktu <= 10:
        stopwatch[2] = 0
    elif 10 < waktu < 12:
        stopwatch[2] = (waktu - 10) / (12 - 10)
    else:
        stopwatch[2] = 1
    
    # Biaya Listrik Membership Functions
    # Biaya Normal: [0, 7600, 13000]
    if biaya <= 7600:
        biayalistrik[0] = 1
    elif 7600 < biaya < 13000:
        biayalistrik[0] = (13000 - biaya) / (13000 - 7600)
    else:
        biayalistrik[0] = 0
        
    # Biaya Mahal: [7600, 13000, 20000]
    if biaya <= 7600:
        biayalistrik[1] = 0
    elif 7600 < biaya < 13000:
        biayalistrik[1] = (biaya - 7600) / (13000 - 7600)
    else:
        biayalistrik[1] = 1
    
    # Debug info with all 5 input values properly printed
    print("Input values:")
    print(f"Daya Listrik (Power): {daya_listrik} KwH (Membership: {Power})")
    print(f"Waktu (Stopwatch): {waktu} jam (Membership: {stopwatch})")
    print(f"Hasil Daya: {Daya} watt (Membership: {HasilDaya})")
    print(f"Jumlah Perangkat: {Sum_perangkat} (Membership: {jumlahperangkat})")
    print(f"Biaya: {biaya} (Membership: {biayalistrik})")
    
    # Initialize rule activation values and defuzzification variables
    rule_values = {}
    numerator = 0
    denominator = 0
    
    # Evaluate all rules
    for i in range(3):  # Power
        for j in range(3):  # stopwatch
            for k in range(3):  # HasilDaya
                for l in range(3):  # jumlahperangkat
                    for m in range(2):  # biayalistrik
                        # Determine output class based on rule
                        if i == 0:  # Power Rendah
                            output_class = penggunaan_Rendah
                        elif i == 1:  # Power Sedang
                            if j == 0:  # stopwatch Cepat
                                output_class = penggunaan_Rendah
                            else:  # stopwatch Normal or Lama
                                output_class = penggunaan_normal
                        else:  # Power Tinggi
                            if j == 0:  # stopwatch Cepat
                                output_class = penggunaan_Rendah
                            elif j == 1:  # stopwatch Normal
                                output_class = penggunaan_normal
                            else:  # stopwatch Lama
                                output_class = penggunaan_tinggi
                        
                        # Calculate rule strength using min operator
                        rule_strength = min(Power[i], stopwatch[j], HasilDaya[k], jumlahperangkat[l], biayalistrik[m])
                        
                        # Accumulate for defuzzification
                        numerator += rule_strength * output_class
                        denominator += rule_strength
                        
                        # Store rule value for debugging
                        rule_name = f"Rule_{i}_{j}_{k}_{l}_{m}"
                        rule_values[rule_name] = rule_strength
    
    # Defuzzification (weighted average)
    if denominator == 0:  # Avoid division by zero
        z = 0
    else:
        z = numerator / denominator
    
    print(f"Defuzzification result (z): {z}")
    
    # Determine output classification
    if z <= 0.67:
        return {
            "fuzy": round(z, 2),
            "text": "Penggunaan Rendah"
        }
    elif z <= 1.33:
        return {
            "fuzy": round(z, 2),
            "text": "Penggunaan Sedang"
        }
    else:
        return {
            "fuzy": round(z, 2),
            "text": "Penggunaan Tinggi"
        }


def response(code, msg, data):
    return Response(status=code, response=json.dumps({
        "status": code == 200,
        "code": code,
        "msg": msg,
        "data": data
    }), mimetype='application/json', headers={'Access-Control-Allow-Origin': '*'})


def biaya(daya, total):
    if daya <= 900:
        return total * 1352
    elif daya <= 1300 or daya <= 2200:
        return total * 1452
    elif daya <= 3500 or daya <= 5500:
        return total * 1699


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


# Inisialisasi client Firestore
db = firestore.Client()


def getData(arrayWaktu, daya):
    dataFuzy = []
    resultTable = []
    energyTotal = 0
    hargaTotal = 0
    
    # Definisikan zona waktu Firestore (UTC) dan zona waktu lokal (Asia/Jakarta)
    utc_timezone = pytz.timezone('UTC')  # Firestore menyimpan data di UTC
    local_timezone = pytz.timezone('Asia/Jakarta')  # UI menggunakan UTC+7
    
    if len(arrayWaktu) <= 0:
        return response(400, "Bad Request", data=None)

    for i in range(len(arrayWaktu)):
        # Parse tanggal input
        dt = datetime.strptime(arrayWaktu[i], "%Y-%m-%d")
        
        # Buat start_of_day dan end_of_day di timezone UTC (sesuai Firestore)
        # Pertama buat di local timezone lalu konversi ke UTC untuk query
        local_start_of_day = local_timezone.localize(datetime(dt.year, dt.month, dt.day, 0, 0, 0, 0))
        local_end_of_day = local_timezone.localize(datetime(dt.year, dt.month, dt.day, 23, 59, 59, 999999))
        
        # Konversi ke UTC untuk query Firestore
        utc_start_of_day = local_start_of_day.astimezone(utc_timezone)
        utc_end_of_day = local_end_of_day.astimezone(utc_timezone)
        
        # Query Firestore dengan timestamp UTC
        day_entries = (
            db.collection("DataBase1Jalur")
            .where(filter=FieldFilter("TimeStamp", ">=", utc_start_of_day))
            .where(filter=FieldFilter("TimeStamp", "<=", utc_end_of_day))
            .get()
        )
        
        # Debug - print jumlah entri yang ditemukan
        print(f"Found {len(day_entries)} entries for {arrayWaktu[i]}")
        
        if len(day_entries) == 0:
            print(f"No entries found for {arrayWaktu[i]}")
            continue
        
        # Pastikan semua entries memiliki TimeStamp
        valid_entries = [entry for entry in day_entries if 'TimeStamp' in entry.to_dict()]
        
        if not valid_entries:
            print(f"No valid entries with TimeStamp for {arrayWaktu[i]}")
            continue
        
        # Sort dan ambil entry dengan timestamp terbaru
        latest_entry = max(valid_entries, key=lambda x: x.to_dict().get('TimeStamp'))
        dataTerakhir = latest_entry.to_dict()
        
        # Konversi timestamp dari Firestore (UTC) ke timezone lokal (Asia/Jakarta)
        firestore_timestamp = dataTerakhir.get('TimeStamp')
        local_timestamp = firestore_timestamp.astimezone(local_timezone) if firestore_timestamp.tzinfo else local_timezone.localize(firestore_timestamp)
        
        print(f"Selected latest entry for {arrayWaktu[i]}: TimeStamp={local_timestamp}, Energy={dataTerakhir.get('energy')}")
        
        # Hitung waktu yang berlalu dalam timezone lokal
        # Menggunakan timestamp lokal untuk perhitungan yang akurat sesuai dengan waktu di UI
        elapsed_hours = (local_timestamp - local_start_of_day).total_seconds() / 3600
        stopwatch = round(elapsed_hours)
        
        # Handle kasus energy yang berbeda penulisan
        energyTerakhir = 0.00
        if 'energy' in dataTerakhir:
            energyTerakhir = dataTerakhir['energy']
        elif 'Energy' in dataTerakhir:
            energyTerakhir = dataTerakhir['Energy']
        
        # Handle JumlahPerangkat
        dataPerangkat = 0
        if 'JumlahPerangkat' in dataTerakhir:
            dataPerangkat = dataTerakhir['JumlahPerangkat']
            
        # Fungsi fuzzy logic
        dataFuzy.append({
            "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d - %m - %Y"),
            "dataFuzy": fuzzyLogic(energyTerakhir, 3, daya, stopwatch, dataTerakhir['HargaListrik']),
        })
        
        # Tabel hasil
        resultTable.append({
            "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d %B %Y"),
            "power": dataPerangkat,
            "energy": energyTerakhir,
            "biaya": "Rp. "+formatRupiah(round(biaya(daya, energyTerakhir))),
            "stopwatch": stopwatch,
            "jumlah": dataTerakhir['JumlahPerangkat'] if 'JumlahPerangkat' in dataTerakhir else 0
        })
        
        energyTotal += energyTerakhir
        hargaTotal += biaya(daya, energyTerakhir)

    return {
        "dataFuzy": dataFuzy,
        "resultTable": resultTable,
        "energyTotal": round(energyTotal, 3),
        "hargaTotal": "Rp. "+formatRupiah(round(hargaTotal))
    }


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/', methods=['GET'])
def index():
    return response(200, "OK", "Hello World")


@app.route('/fuzzy', methods=['POST'])
def fuzzys():
    if 'start_date' not in request.json or 'end_date' not in request.json or 'daya' not in request.json:
        return response(400, "Bad Request", data=None)

    start_date = request.json['start_date']
    end_date = request.json['end_date']
    daya = request.json['daya']
    print("request", start_date, end_date, daya)

    dtrange = pd.date_range(start=start_date, end=end_date, freq='d')
    arrayWaktu = []
    for dt in dtrange:
        arrayWaktu.append(dt.strftime("%Y-%m-%d"))
    data = getData(arrayWaktu, daya)
    print("response", data)
    return response(200, "OK", data=data)


if __name__ == "__main__":
    print("Server is running on port 5000")
    app.run(host="0.0.0.0", port=os.getenv('PORT', 5000))