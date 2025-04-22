from flask import Flask, render_template, request, redirect, url_for, Response
import json
import time
from datetime import datetime
from flask_cors import CORS
import pandas as pd
import os
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

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
    # sensor daya listrik
    # RENDAH	0	0,66	1
    # SEDANG	0,833	1,66	2,5
    # TINGGI	2,33	3,66	4
    # #dayalistrik rendah
    if daya_listrik < 0.66:
        Power[0] = 1
    elif daya_listrik < 1:
        Power[0] = (1 - daya_listrik)/(1 - 0.83)
    else:
        Power[0] = 0

    # dayalistrik Sedang
    if daya_listrik < 0.83:
        Power[1] = 0
    elif daya_listrik < 1.66:
        Power[1] = (daya_listrik-0.83)/(1.6 - 0.83)
    elif daya_listrik < 2.5:
        Power[1] = (2.5-daya_listrik)/(2.5 - 1.6)
    else:
        Power[1] = 0

    # dayalistrik Tinggi
    if daya_listrik < 2.33:
        Power[2] = 0
    elif daya_listrik < 3.66:
        Power[2] = (daya_listrik-3.66)/(3.66 - 2.33)
    else:
        Power[2] = 1

    # inputan banyak perangkat
    # sedikit		0	4
    # Sedang	1	1,5-2,5	3
    # Banyak	2,5	3-x	x

    # jumlahperangkatumah sedikit
    if Sum_perangkat < 2:
        jumlahperangkat[0] = 1
    elif Sum_perangkat < 4:
        jumlahperangkat[0] = (4 - Sum_perangkat)/(4 - 2)
    else:
        jumlahperangkat[0] = 0

    # jumlahperangkatumah sedang
    if Sum_perangkat < 2:
        jumlahperangkat[1] = 0
    elif Sum_perangkat < 4:
        jumlahperangkat[1] = (Sum_perangkat - 2)/(4 - 2)
    elif Sum_perangkat < 6:
        jumlahperangkat[1] = 1
    elif Sum_perangkat < 8:
        jumlahperangkat[1] = (8 - Sum_perangkat)/(8 - 6)
    else:
        jumlahperangkat[1] = 0

    # jumlahperangkatumah Banyak
    if Sum_perangkat < 6:
        jumlahperangkat[2] = 0
    elif Sum_perangkat < 8:
        jumlahperangkat[2] = (Sum_perangkat-6)/(8 - 6)
    else:
        jumlahperangkat[2] = 1

    # inputan Daya Listrik
    # Rendah	x	400	900
    # Normal	400	900	1400
    # Tinggi	900	1400	x

    # Daya rendah
    if Daya < 400:
        HasilDaya[0] = 1
    elif Daya < 900:
        HasilDaya[0] = (900 - Daya)/(900 - 400)
    else:
        HasilDaya[0] = 0

    # HasilDayasedang
    if Daya < 400:
        HasilDaya[1] = 0
    elif Daya < 900:
        HasilDaya[1] = (Daya-400)/(900 - 400)
    elif Daya < 1400:
        HasilDaya[1] = (1400 - Daya)/(1400-900)
    else:
        HasilDaya[1] = 0

    # HasilDaya Banyak
    if Daya < 900:
        HasilDaya[2] = 0
    elif Daya < 1400:
        HasilDaya[2] = (Daya-900)/(1400-900)
    else:
        HasilDaya[2] = 1

    # Inputan waktu Penggunaan
    # Cepat		0-6	8
    # Normal	6	8-12	14
    # Lama	12	14-24	24

    if waktu < 6:
        stopwatch[0] = 1
    elif waktu < 8:
        stopwatch[0] = (8 - waktu)/(8 - 6)
    else:
        stopwatch[0] = 0

    # stopwatchumah sedang
    if waktu < 6:
        stopwatch[1] = 0
    elif waktu < 8:
        stopwatch[1] = (waktu - 6)/(8 - 6)
    elif waktu < 10:
        stopwatch[1] = 1
    elif waktu < 12:
        stopwatch[1] = (12 - waktu)/(12 - 10)
    else:
        stopwatch[1] = 0

    # stopwatchumah Banyak
    if waktu < 10:
        stopwatch[2] = 0
    elif waktu < 12:
        stopwatch[2] = (waktu-10)/(12 - 10)
    else:
        stopwatch[2] = 1

    # biaya listrik murah
    if biaya < 4000:
        biayalistrik[0] = 1
    elif biaya < 7000:
        biayalistrik[0] = (7000 - biaya)/(7000 - 4000)
    else:
        biayalistrik[0] = 0

    # biaya mahal
    if biaya < 4000:
        biayalistrik[1] = 0
    elif biaya < 7000:
        biayalistrik[1] = (biaya - 4000)/(7000 - 4000)
    else:
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
    if len(arrayWaktu) <= 0:
        return response(400, "Bad Request", data=None)

    # Inisialisasi client Firestore di luar loop jika belum ada
    db = firestore.Client()

    for i in range(len(arrayWaktu)):
        dt = datetime.strptime(arrayWaktu[i], "%Y-%m-%d")
        print(f"Processing date: {arrayWaktu[i]}")
        
        # Dapatkan semua data dari koleksi
        all_docs = db.collection("DataBase1Jalur").get()
        matching_docs = []
        
        # Filter dokumen secara manual berdasarkan tanggal
        for doc in all_docs:
            doc_data = doc.to_dict()
            if 'TimeStamp' in doc_data:
                # TimeStamp bisa dalam berbagai format, coba tangani keduanya
                ts = doc_data['TimeStamp']
                timestamp_date = None
                
                # Jika TimeStamp adalah string
                if isinstance(ts, str):
                    try:
                        # Contoh format: "April 21, 2025 at 11:59:38 PM UTC+7"
                        # Ekstrak tanggal dari string
                        date_part = ts.split(" at ")[0]
                        timestamp_date = datetime.strptime(date_part, "%B %d, %Y")
                    except Exception as e:
                        print(f"Error parsing string timestamp: {e}")
                        continue
                # Jika TimeStamp adalah objek datetime
                elif hasattr(ts, 'year'):
                    timestamp_date = ts
                
                # Jika berhasil mendapatkan tanggal, bandingkan dengan tanggal yang diminta
                if timestamp_date and timestamp_date.date() == dt.date():
                    matching_docs.append(doc)
                    print(f"Found matching document for {arrayWaktu[i]}: {doc_data}")
        
        print(f"Total matching documents for {arrayWaktu[i]}: {len(matching_docs)}")
        
        # Jika tidak ada dokumen yang cocok
        if len(matching_docs) == 0:
            print(f"No data found for date {arrayWaktu[i]}")
            dataFuzy.append({
                "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d - %m - %Y"),
                "dataFuzy": {
                    "fuzy": 0.0,
                    "text": "Data Tidak Tersedia"
                },
            })
            
            resultTable.append({
                "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d %B %Y"),
                "power": 0,
                "energy": 0,
                "biaya": "Rp. 0",
                "stopwatch": 0,
                "jumlah": 0
            })
            continue
        
        # Urutkan dokumen yang cocok berdasarkan waktu (ambil yang terbaru untuk tanggal yang diminta)
        # Kita bisa mencoba menyortir secara manual berdasarkan waktu jika TimeStamp adalah string
        latest_doc = None
        latest_time = None
        
        for doc in matching_docs:
            doc_data = doc.to_dict()
            ts = doc_data['TimeStamp']
            
            # Jika TimeStamp adalah string
            if isinstance(ts, str):
                try:
                    # Contoh format: "April 21, 2025 at 11:59:38 PM UTC+7"
                    time_part = ts.split(" at ")[1].split(" UTC")[0]
                    date_part = ts.split(" at ")[0]
                    full_time_str = f"{date_part} {time_part}"
                    # Coba beberapa format umum
                    time_formats = [
                        "%B %d, %Y %I:%M:%S %p",
                        "%B %d, %Y %H:%M:%S"
                    ]
                    parsed_time = None
                    for fmt in time_formats:
                        try:
                            parsed_time = datetime.strptime(full_time_str, fmt)
                            break
                        except:
                            continue
                    
                    if parsed_time and (latest_time is None or parsed_time > latest_time):
                        latest_time = parsed_time
                        latest_doc = doc
                except Exception as e:
                    print(f"Error parsing time from timestamp: {e}")
            # Jika TimeStamp adalah objek datetime
            elif hasattr(ts, 'hour'):
                if latest_time is None or ts > latest_time:
                    latest_time = ts
                    latest_doc = doc
        
        if latest_doc is None:
            print(f"No valid timestamp found for {arrayWaktu[i]}")
            continue
            
        # Gunakan dokumen terbaru untuk tanggal yang diminta
        dataTerakhir = latest_doc.to_dict()
        print(f"Latest document for {arrayWaktu[i]}: {dataTerakhir}")
        
        # Hitung stopwatch (waktu penggunaan dalam jam)
        stopwatch = 0
        if isinstance(dt, datetime):
            # Asumsi penggunaan sepanjang hari jika tidak ada waktu spesifik
            stopwatch = 24  # 24 jam
        else:
            # Jika ada informasi waktu yang lebih spesifik, bisa digunakan di sini
            stopwatch = 24  # Default ke 24 jam
        
        # Ambil nilai energy dari dokumen
        energyTerakhir = 0.0
        if 'energy' in dataTerakhir:
            energyTerakhir = float(dataTerakhir['energy'])
        elif 'Energy' in dataTerakhir:
            energyTerakhir = float(dataTerakhir['Energy'])
        print(f"Energy value: {energyTerakhir}")
        
        # Ambil jumlah perangkat
        dataPerangkat = 0
        if 'JumlahPerangkat' in dataTerakhir:
            dataPerangkat = float(dataTerakhir['JumlahPerangkat'])
        print(f"Jumlah perangkat: {dataPerangkat}")
        
        # Ambil harga listrik
        hargaListrik = 0
        if 'HargaListrik' in dataTerakhir:
            hargaListrik = float(dataTerakhir['HargaListrik'])
        print(f"Harga listrik: {hargaListrik}")
        
        # Hitung fuzzy logic
        resultFuzzy = fuzzyLogic(energyTerakhir, dataPerangkat or 1, daya, stopwatch, hargaListrik)
        print(f"Fuzzy result: {resultFuzzy}")
        
        dataFuzy.append({
            "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d - %m - %Y"),
            "dataFuzy": resultFuzzy,
        })
        
        resultTable.append({
            "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d %B %Y"),
            "power": dataPerangkat,
            "energy": energyTerakhir,
            "biaya": "Rp. "+formatRupiah(round(biaya(daya, energyTerakhir))),
            "stopwatch": stopwatch,
            "jumlah": dataPerangkat
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