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
    # input Fuzzy
    daya_listrik = float(Power)
    Sum_perangkat = float(jumlahperangkat)
    Daya = float(HasilDaya)
    waktu = float(stopwatch)
    biaya = float(biayalistrik)

    Power = [0, 0, 0]
    jumlahperangkat = [0, 0, 0]
    HasilDaya = [0, 0, 0]
    stopwatch = [0, 0, 0]
    biayalistrik = [0, 0]
    # 3333

    rules = [[
            [[[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]]],
            [[[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]]],
            [[[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]]]],
             [
        [[[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]]],
        [[[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]]],
        [[[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]]]],
        [
        [[[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]],
         [[0, 0], [0, 0], [0, 0]]],
            [[[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]]],
            [[[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]],
             [[0, 0], [0, 0], [0, 0]]]]
    ]

    penggunaan_Rendah = 0
    penggunaan_normal = 1
    penggunaan_tinggi = 2

    # fuzzyfication
    # energy listrik
    # RENDAH	0	0,66	1
    # SEDANG	0,833	1,66	2,5
    # TINGGI	2,33	3,66	4
    # energylistrik rendah


   ## b. Fungsi keanggotaan KwH
    # KwH Rendah
    if daya_listrik <= 0.66:
        Power[0] = 1
    elif 0.66 < daya_listrik < 0.83:
        Power[0] = (0.83 - daya_listrik) / (0.83 - 0.66)
    else:  # daya_listrik >= 0.83
        Power[0] = 0

    # KwH Sedang
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

    # KwH Tinggi
    if daya_listrik <= 1.66:
        Power[2] = 0
    elif 1.66 < daya_listrik < 2.5:
        Power[2] = (daya_listrik - 1.66) / (2.5 - 1.66)
    else:  # daya_listrik >= 2.5
        Power[2] = 1


    ## d. Fungsi keanggotaan Jumlah Perangkat
    # Jumlah Perangkat Sedikit
    if Sum_perangkat <= 2:
        jumlahperangkat[0] = 1
    elif 2 < Sum_perangkat < 4:
        jumlahperangkat[0] = (4 - Sum_perangkat) / (4 - 2)
    else:  # Sum_perangkat >= 4
        jumlahperangkat[0] = 0

    # Jumlah Perangkat Sedang
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

    # Jumlah Perangkat Banyak
    if Sum_perangkat <= 6:
        jumlahperangkat[2] = 0
    elif 6 < Sum_perangkat < 8:
        jumlahperangkat[2] = (Sum_perangkat - 6) / (8 - 6)
    else:  # Sum_perangkat >= 8
        jumlahperangkat[2] = 1

    # inputan Daya Listrik
    # Rendah	x	400	900
    # Normal	400	900	1400
    # Tinggi	900	1400	x

    ## c. Fungsi keanggotaan Daya Listrik
    # Daya Listrik Rendah
    if Daya <= 900:
        HasilDaya[0] = 1
    elif 900 < Daya < 1300:
        HasilDaya[0] = (1300 - Daya) / (1300 - 900)
    else:  # Daya >= 1300
        HasilDaya[0] = 0

    # Daya Listrik Sedang
    if Daya <= 900 or Daya >= 2200:
        HasilDaya[1] = 0
    elif 900 < Daya <= 1300:
        HasilDaya[1] = (Daya - 900) / (1300 - 900)
    elif 1300 < Daya < 2200:
        HasilDaya[1] = (2200 - Daya) / (2200 - 1300)
    else:
        HasilDaya[1] = 0

    # Daya Listrik Tinggi
    if Daya <= 1300:
        HasilDaya[2] = 0
    elif 1300 < Daya < 2200:
        HasilDaya[2] = (Daya - 1300) / (2200 - 1300)
    else:  # Daya >= 2200
        HasilDaya[2] = 1

    # Inputan waktu Penggunaan
    # Cepat		0-6	8
    # Normal	6	8-12	14
    # Lama	12	14-24	24

    ## a. Fungsi keanggotaan waktu pengguna
    # Waktu Cepat
    if waktu <= 6:
        stopwatch[0] = 1
    elif 6 < waktu < 8:
        stopwatch[0] = (8 - waktu) / (8 - 6)
    else:  # waktu >= 8
        stopwatch[0] = 0

    # Waktu Sedang
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

    # Waktu Lama
    if waktu <= 10:
        stopwatch[2] = 0
    elif 10 < waktu < 12:
        stopwatch[2] = (waktu - 10) / (12 - 10)
    else:  # waktu >= 12
        stopwatch[2] = 1

    # Biaya Listrik Normal
    if biaya <= 7600:
        biayalistrik[0] = 1
    elif 7600 < biaya < 13000:
        biayalistrik[0] = (13000 - biaya) / (13000 - 7600)
    else:  # biaya >= 13000
        biayalistrik[0] = 0

    # Biaya Listrik Mahal
    if biaya <= 7600:
        biayalistrik[1] = 0
    elif 7600 < biaya < 13000:
        biayalistrik[1] = (biaya - 7600) / (13000 - 7600)
    else:  # biaya >= 13000
        biayalistrik[1] = 1
    # end fuzzyfication

    print(waktu)
    print(stopwatch)
    print(daya_listrik)
    print(Power)
    print(Daya)
    print(HasilDaya)
    print(Sum_perangkat)
    print(jumlahperangkat)
    print(biaya)
    print(biayalistrik)

    defuzzy = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    for m in range(2):
                        print('i:', i, ' j:', j, ' k:', k, 'l:', l, 'm:', m)
                        rules[i][j][k][l][m] = min(
                            stopwatch[j], Power[i], HasilDaya[k], jumlahperangkat[l], biayalistrik[m])
                        defuzzy += rules[i][j][k][l][m]

    z = (
        # 1
        (rules[0][0][0][0][0] * penggunaan_Rendah)+(rules[0][0][1][0][0] * penggunaan_Rendah)+(rules[0][0][2][0][0] * penggunaan_Rendah) +
        (rules[0][1][0][0][0] * penggunaan_Rendah)+(rules[0][1][1][0][0] * penggunaan_Rendah)+(rules[0][1][2][0][0] * penggunaan_Rendah) +
        (rules[0][2][0][0][0] * penggunaan_Rendah)+(rules[0][2][1][0][0] * penggunaan_Rendah)+(rules[0][2][2][0][0] * penggunaan_Rendah) +
        (rules[1][0][0][0][0] * penggunaan_Rendah)+(rules[1][0][1][0][0] * penggunaan_Rendah)+(rules[1][0][2][0][0] * penggunaan_Rendah) +
        (rules[1][1][0][0][0] * penggunaan_normal)+(rules[1][1][1][0][0] * penggunaan_normal)+(rules[1][1][2][0][0] * penggunaan_normal) +
        (rules[1][2][0][0][0] * penggunaan_normal)+(rules[1][2][1][0][0] * penggunaan_normal)+(rules[1][2][2][0][0] * penggunaan_normal) +
        (rules[2][0][0][0][0] * penggunaan_Rendah)+(rules[2][0][1][0][0] * penggunaan_Rendah)+(rules[2][0][2][0][0] * penggunaan_Rendah) +
        (rules[2][1][0][0][0] * penggunaan_normal)+(rules[2][1][1][0][0] * penggunaan_normal)+(rules[2][1][2][0][0] * penggunaan_normal) +
        (rules[2][2][0][0][0] * penggunaan_tinggi)+(rules[2][2][1][0][0] * penggunaan_tinggi)+(rules[2][2][2][0][0] * penggunaan_tinggi) +

        # 2
        (rules[0][0][0][1][0] * penggunaan_Rendah)+(rules[0][0][1][1][0] * penggunaan_Rendah)+(rules[0][0][2][1][0] * penggunaan_Rendah) +
        (rules[0][1][0][1][0] * penggunaan_Rendah)+(rules[0][1][1][1][0] * penggunaan_Rendah)+(rules[0][1][2][1][0] * penggunaan_Rendah) +
        (rules[0][2][0][1][0] * penggunaan_Rendah)+(rules[0][2][1][1][0] * penggunaan_Rendah)+(rules[0][2][2][1][0] * penggunaan_Rendah) +
        (rules[1][0][0][1][0] * penggunaan_Rendah)+(rules[1][0][1][1][0] * penggunaan_Rendah)+(rules[1][0][2][1][0] * penggunaan_Rendah) +
        (rules[1][1][0][1][0] * penggunaan_normal)+(rules[1][1][1][1][0] * penggunaan_normal)+(rules[1][1][2][1][0] * penggunaan_normal) +
        (rules[1][2][0][1][0] * penggunaan_normal)+(rules[1][2][1][1][0] * penggunaan_normal)+(rules[1][2][2][1][0] * penggunaan_normal) +
        (rules[2][0][0][1][0] * penggunaan_Rendah)+(rules[2][0][1][1][0] * penggunaan_Rendah)+(rules[2][0][2][1][0] * penggunaan_Rendah) +
        (rules[2][1][0][1][0] * penggunaan_normal)+(rules[2][1][1][1][0] * penggunaan_normal)+(rules[2][1][2][1][0] * penggunaan_normal) +
        (rules[2][2][0][1][0] * penggunaan_tinggi)+(rules[2][2][1][1][0] * penggunaan_tinggi)+(rules[2][2][2][1][0] * penggunaan_tinggi) +

        # 3
        (rules[0][0][0][2][0] * penggunaan_Rendah)+(rules[0][0][1][2][0] * penggunaan_Rendah)+(rules[0][0][2][2][0] * penggunaan_Rendah) +
        (rules[0][1][0][2][0] * penggunaan_Rendah)+(rules[0][1][1][2][0] * penggunaan_Rendah)+(rules[0][1][2][2][0] * penggunaan_Rendah) +
        (rules[0][2][0][2][0] * penggunaan_Rendah)+(rules[0][2][1][2][0] * penggunaan_Rendah)+(rules[0][2][2][2][0] * penggunaan_Rendah) +
        (rules[1][0][0][2][0] * penggunaan_Rendah)+(rules[1][0][1][2][0] * penggunaan_Rendah)+(rules[1][0][2][2][0] * penggunaan_Rendah) +
        (rules[1][1][0][2][0] * penggunaan_normal)+(rules[1][1][1][2][0] * penggunaan_normal)+(rules[1][1][2][2][0] * penggunaan_normal) +
        (rules[1][2][0][2][0] * penggunaan_normal)+(rules[1][2][1][2][0] * penggunaan_normal)+(rules[1][2][2][2][0] * penggunaan_normal) +
        (rules[2][0][0][2][0] * penggunaan_Rendah)+(rules[2][0][1][2][0] * penggunaan_Rendah)+(rules[2][0][2][2][0] * penggunaan_Rendah) +
        (rules[2][1][0][2][0] * penggunaan_normal)+(rules[2][1][1][2][0] * penggunaan_normal)+(rules[2][1][2][2][0] * penggunaan_normal) +
        (rules[2][2][0][2][0] * penggunaan_tinggi)+(rules[2][2][1][2][0] * penggunaan_tinggi)+(rules[2][2][2][2][0] * penggunaan_tinggi) +

        # 1
        (rules[0][0][0][0][1] * penggunaan_Rendah)+(rules[0][0][1][0][1] * penggunaan_Rendah)+(rules[0][0][2][0][1] * penggunaan_Rendah) +
        (rules[0][1][0][0][1] * penggunaan_Rendah)+(rules[0][1][1][0][1] * penggunaan_Rendah)+(rules[0][1][2][0][1] * penggunaan_Rendah) +
        (rules[0][2][0][0][1] * penggunaan_Rendah)+(rules[0][2][1][0][1] * penggunaan_Rendah)+(rules[0][2][2][0][1] * penggunaan_Rendah) +
        (rules[1][0][0][0][1] * penggunaan_Rendah)+(rules[1][0][1][0][1] * penggunaan_Rendah)+(rules[1][0][2][0][1] * penggunaan_Rendah) +
        (rules[1][1][0][0][1] * penggunaan_normal)+(rules[1][1][1][0][1] * penggunaan_normal)+(rules[1][1][2][0][1] * penggunaan_normal) +
        (rules[1][2][0][0][1] * penggunaan_normal)+(rules[1][2][1][0][1] * penggunaan_normal)+(rules[1][2][2][0][1] * penggunaan_normal) +
        (rules[2][0][0][0][1] * penggunaan_Rendah)+(rules[2][0][1][0][1] * penggunaan_Rendah)+(rules[2][0][2][0][1] * penggunaan_Rendah) +
        (rules[2][1][0][0][1] * penggunaan_normal)+(rules[2][1][1][0][1] * penggunaan_normal)+(rules[2][1][2][0][1] * penggunaan_normal) +
        (rules[2][2][0][0][1] * penggunaan_tinggi)+(rules[2][2][1][0][1] * penggunaan_tinggi)+(rules[2][2][2][0][1] * penggunaan_tinggi) +

        # 2
        (rules[0][0][0][1][1] * penggunaan_Rendah)+(rules[0][0][1][1][1] * penggunaan_Rendah)+(rules[0][0][2][1][1] * penggunaan_Rendah) +
        (rules[0][1][0][1][1] * penggunaan_Rendah)+(rules[0][1][1][1][1] * penggunaan_Rendah)+(rules[0][1][2][1][1] * penggunaan_Rendah) +
        (rules[0][2][0][1][1] * penggunaan_Rendah)+(rules[0][2][1][1][1] * penggunaan_Rendah)+(rules[0][2][2][1][1] * penggunaan_Rendah) +
        (rules[1][0][0][1][1] * penggunaan_Rendah)+(rules[1][0][1][1][1] * penggunaan_Rendah)+(rules[1][0][2][1][1] * penggunaan_Rendah) +
        (rules[1][1][0][1][1] * penggunaan_normal)+(rules[1][1][1][1][1] * penggunaan_normal)+(rules[1][1][2][1][1] * penggunaan_normal) +
        (rules[1][2][0][1][1] * penggunaan_normal)+(rules[1][2][1][1][1] * penggunaan_normal)+(rules[1][2][2][1][1] * penggunaan_normal) +
        (rules[2][0][0][1][1] * penggunaan_Rendah)+(rules[2][0][1][1][1] * penggunaan_Rendah)+(rules[2][0][2][1][1] * penggunaan_Rendah) +
        (rules[2][1][0][1][1] * penggunaan_normal)+(rules[2][1][1][1][1] * penggunaan_normal)+(rules[2][1][2][1][1] * penggunaan_normal) +
        (rules[2][2][0][1][1] * penggunaan_tinggi)+(rules[2][2][1][1][1] * penggunaan_tinggi)+(rules[2][2][2][1][1] * penggunaan_tinggi) +
        # 3
        (rules[0][0][0][2][1] * penggunaan_Rendah)+(rules[0][0][1][2][1] * penggunaan_Rendah)+(rules[0][0][2][2][1] * penggunaan_Rendah) +
        (rules[0][1][0][2][1] * penggunaan_Rendah)+(rules[0][1][1][2][1] * penggunaan_Rendah)+(rules[0][1][2][2][1] * penggunaan_Rendah) +
        (rules[0][2][0][2][1] * penggunaan_Rendah)+(rules[0][2][1][2][1] * penggunaan_Rendah)+(rules[0][2][2][2][1] * penggunaan_Rendah) +
        (rules[1][0][0][2][1] * penggunaan_Rendah)+(rules[1][0][1][2][1] * penggunaan_Rendah)+(rules[1][0][2][2][1] * penggunaan_Rendah) +
        (rules[1][1][0][2][1] * penggunaan_normal)+(rules[1][1][1][2][1] * penggunaan_normal)+(rules[1][1][2][2][1] * penggunaan_normal) +
        (rules[1][2][0][2][1] * penggunaan_normal)+(rules[1][2][1][2][1] * penggunaan_normal)+(rules[1][2][2][2][1] * penggunaan_normal) +
        (rules[2][0][0][2][1] * penggunaan_Rendah)+(rules[2][0][1][2][1] * penggunaan_Rendah)+(rules[2][0][2][2][1] * penggunaan_Rendah) +
        (rules[2][1][0][2][1] * penggunaan_normal)+(rules[2][1][1][2][1] * penggunaan_normal)+(rules[2][1][2][2][1] * penggunaan_normal) +
        (rules[2][2][0][2][1] * penggunaan_tinggi)+(rules[2][2][1][2][1] * penggunaan_tinggi)+(rules[2][2][2][2][1] * penggunaan_tinggi))/defuzzy

    print("Z adalah : "+str(z))

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