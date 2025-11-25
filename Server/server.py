from flask import Flask, request, jsonify
from datetime import datetime, timedelta # 📌 PERUBAHAN 1: Import timedelta
import csv
import os
import fuzzy_logic
from package_map import PACKAGE_NAME_MAP, APP_CATEGORY_MAP
import json 

app = Flask(__name__)

# Global values from IoT
LAST_TEMPERATURE = 25
LAST_HUMIDITY = 30
LAST_AIRQUALITY = 20
# 📌 PERUBAHAN 2: Tambahkan variabel untuk menyimpan timestamp IoT terakhir
LAST_IOT_TIMESTAMP = datetime.min # Diinisialisasi dengan waktu minimal

# Tentukan ambang batas proksimitas (misal: 5 menit)
TIME_PROXIMITY_THRESHOLD = timedelta(minutes=5) 

SMARTPHONE_DATA_RECEIVED = False # Tetap hanya untuk pesan info awal

def format_hms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours} jam {minutes} menit {secs} detik"

# Variabel CSV harus konsisten
CSV_OVERALL = "dataset_overall.csv" 

# Create CSVs if not exist
if not os.path.exists(CSV_OVERALL):
    with open(CSV_OVERALL, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "source", 
            "temperature", "humidity", "air_quality", 
            "app_count", "total_usage_time", "fuzzy_level", "message",
            "usage_details" 
        ])
# =======================
# ENDPOINT: ANDROID
# =======================
@app.route('/receive_usage', methods=['POST'])
def receive_usage():
    # 📌 PERUBAHAN 3: Tambahkan LAST_IOT_TIMESTAMP ke global
    global LAST_TEMPERATURE, LAST_HUMIDITY, LAST_AIRQUALITY, SMARTPHONE_DATA_RECEIVED, LAST_IOT_TIMESTAMP 

    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "error", "message": "no json received"}), 400

    if not SMARTPHONE_DATA_RECEIVED:
        SMARTPHONE_DATA_RECEIVED = True
        print("\n[INFO] Data Smartphone Pertama Diterima. Data IoT Sekarang Diizinkan Tampil dan Disimpan.")

    total_sec_all = data.get("total_screen_time_s", 0)
    usage_list = data.get("usage_data", [])

    now_dt = datetime.now() # Ambil waktu sekarang sebagai objek datetime
    now = now_dt.isoformat()
    formatted_total = format_hms(total_sec_all)
    total_hours = total_sec_all / 3600

    # Fuzzy logic using IoT sensor values (Selalu menggunakan nilai global terbaru)
    result = fuzzy_logic.calculate_stress(
        total_hours,
        LAST_TEMPERATURE,
        LAST_HUMIDITY,
        LAST_AIRQUALITY
    )

    level = result["category"]
    message = result["message"] # Pesan dari hasil fuzzy logic

    print(f"\n[{now}] === Android Usage Data ===")
    print(f"Total Screen Time: {formatted_total} → Level: {level}")
    print(f"Suhu dipakai: {LAST_TEMPERATURE}°C, Humid: {LAST_HUMIDITY}%, AQ: {LAST_AIRQUALITY}%")
    print(f"Jumlah Aplikasi: {len(usage_list)}")
    print(f"FUZZY MESSAGE: {message}") 

    # Proses usage_list menjadi JSON String yang tersimpan
    detailed_usage = []
    for item in usage_list:
        pkg = item.get("package")
        app_name = PACKAGE_NAME_MAP.get(pkg, pkg)
        category = APP_CATEGORY_MAP.get(pkg, "Lainnya")
        
        detailed_usage.append({
            "name": app_name,
            "category": category,
            "time_s": item.get("foreground_time_s", 0)
        })

    try:
        usage_details_json_string = json.dumps(detailed_usage)
    except Exception as e:
        usage_details_json_string = f"Error serializing usage: {e}" 
    
    # Simpan ke CSV (Baris Ringkasan Android)
    with open(CSV_OVERALL, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # 1. Tulis baris Android
        writer.writerow([
            now, "android_summary", 
            LAST_TEMPERATURE, LAST_HUMIDITY, LAST_AIRQUALITY, 
            len(usage_list), formatted_total, level, message,
            usage_details_json_string
        ])
        
        # 📌 PERUBAHAN 4: Cek Proksimitas Waktu IoT
        time_difference = now_dt - LAST_IOT_TIMESTAMP
        
        # Periksa apakah IoT masuk dalam jendela waktu
        if time_difference >= timedelta(seconds=0) and time_difference <= TIME_PROXIMITY_THRESHOLD:
            
            iot_message = f"IoT data (T:{LAST_TEMPERATURE}) saved due to {TIME_PROXIMITY_THRESHOLD} proximity."
            
            # 2. Tulis baris IoT (jika lolos cek proksimitas)
            writer.writerow([
                LAST_IOT_TIMESTAMP.isoformat(), "iot_proximal", 
                LAST_TEMPERATURE, LAST_HUMIDITY, LAST_AIRQUALITY, 
                "", "", "", iot_message,
                ""
            ])
            print(f"[INFO] PROXIMITY LOGGED: Data IoT ({LAST_IOT_TIMESTAMP.strftime('%H:%M:%S')}) disimpan ke CSV.")
        else:
             print(f"[INFO] PROXIMITY CHECK: Data IoT terakhir ({LAST_IOT_TIMESTAMP.strftime('%H:%M:%S')}) terlalu jauh. Tidak disimpan ke CSV.")

    return jsonify({
        "status": "ok",
        "source": "android",
        "message": message,
        # ... (response data lainnya)
    }), 200


# =======================
# ENDPOINT: IoT
# =======================
@app.route('/receive_sensor', methods=['POST'])
def receive_sensor():
    # 📌 PERUBAHAN 5: Tambahkan LAST_IOT_TIMESTAMP ke global
    global LAST_TEMPERATURE, LAST_HUMIDITY, LAST_AIRQUALITY, LAST_IOT_TIMESTAMP

    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "error", "message": "no json received"}), 400

    suhu = data.get("temperature")
    kelembapan = data.get("humidity")
    kualitas_udara = data.get("air_quality")

    # Update global state
    LAST_TEMPERATURE = suhu
    LAST_HUMIDITY = kelembapan
    LAST_AIRQUALITY = kualitas_udara
    LAST_IOT_TIMESTAMP = datetime.now() # 📌 Simpan waktu update IoT

    now = datetime.now().isoformat()
    
    # 📌 PERUBAHAN 6: Hapus semua logika penyimpanan CSV dari sini
    
    message = "Sensor data received and updated global state." 
    
    print(f"\n[{now}] === IoT Sensor Data ===")
    print(f"Suhu: {suhu} °C | Humid: {kelembapan}% | AQ: {kualitas_udara}%")
    print(f"IOT STATUS: {message}") 
        
    return jsonify({
        "status": "ok",
        "source": "iot",
        "message": message, 
        "temperature": suhu,
        "humidity": kelembapan,
        "air_quality": kualitas_udara
    }), 200


# RUN SERVER
if __name__ == "__main__":
    print("Server Flask aktif di http://0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)