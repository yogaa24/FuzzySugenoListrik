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

    for i in range(len(arrayWaktu)):
        dt = datetime.strptime(arrayWaktu[i], "%Y-%m-%d")
        # Set start of day (in local time)
        start_of_day = datetime.replace(dt, hour=0, minute=0, second=0, microsecond=0)
        # Set end of day (in local time)
        end_of_day = datetime.replace(dt, hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"Querying for date: {arrayWaktu[i]}, start: {start_of_day}, end: {end_of_day}")
        
        # Use the FieldFilter for TimeStamp queries
        day_entries = (
            db.collection("DataBase1Jalur")
            .where(filter=FieldFilter("TimeStamp", ">=", start_of_day))
            .where(filter=FieldFilter("TimeStamp", "<=", end_of_day))
            .order_by("TimeStamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .get()
        )

        if len(day_entries) == 0:
            print(f"No entries found for date: {arrayWaktu[i]}")
            # Add default values if no data found for this date
            dataFuzy.append({
                "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d - %m - %Y"),
                "dataFuzy": {
                    "fuzy": 0.0,
                    "text": "Penggunaan Rendah"
                }
            })
            
            resultTable.append({
                "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d %B %Y"),
                "power": 0.0,
                "energy": 0.0,
                "biaya": "Rp. 0",
                "stopwatch": 0,
                "jumlah": 0
            })
            continue

        print(f"Found {len(day_entries)} entries for {arrayWaktu[i]}")
        dataTerakhir = day_entries[0].to_dict()
        print(f"Last document data: {dataTerakhir}")
        
        # Calculate time elapsed from start of day to the last entry
        timeElapse = dataTerakhir['TimeStamp'].replace(
            tzinfo=None) - start_of_day.replace(tzinfo=None)
        stopwatch = round(timeElapse.total_seconds() / 3600)
        
        # Get energy value with proper field name
        energyTerakhir = dataTerakhir.get('energy', 0.0)
        print(f"Energy value: {energyTerakhir}")
            
        # Get jumlah perangkat
        dataPerangkat = dataTerakhir.get('JumlahPerangkat', 0)
        
        # Get or calculate harga listrik
        harga_listrik = dataTerakhir.get('HargaListrik', 0)
        if harga_listrik == 0:
            # Use the field name from your screenshot
            harga_listrik = dataTerakhir.get('HargaListrik', dataTerakhir.get('HargaListrik', 1352))
            
        dataFuzy.append({
            "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d - %m - %Y"),
            "dataFuzy": fuzzyLogic(energyTerakhir, dataPerangkat or 1, daya, stopwatch, harga_listrik),
        })
        
        resultTable.append({
            "waktu": datetime.strptime(arrayWaktu[i], "%Y-%m-%d").strftime("%d %B %Y"),
            "power": dataTerakhir.get('power', 0),
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