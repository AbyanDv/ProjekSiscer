import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# ====================================
# DEFINITION WITH SKFUZZY (Sama seperti yang Anda berikan)
# ====================================

# Universe
screen_universe = np.arange(0, 13, 1) # 0 hingga 12 jam
temp_universe = np.arange(10, 41, 1)  # 10 hingga 40 °C
stress_universe = np.arange(0, 101, 1) # 0 hingga 100
humid_universe = np.arange(0, 101, 1) # 0 hingga 100 %
aq_universe = np.arange(0, 101, 1)    # 0 hingga 100 (misalnya, indeks kualitas udara terbalik)

# Input fuzzy variables
screen = ctrl.Antecedent(screen_universe, "screen") 
temp = ctrl.Antecedent(temp_universe, "temperature")
humid = ctrl.Antecedent(humid_universe, "humidity")
airq = ctrl.Antecedent(aq_universe, "air_quality")

# Output fuzzy variable
stress = ctrl.Consequent(stress_universe, "stress")

# Membership functions
screen['rendah'] = fuzz.trimf(screen_universe, [0, 0, 4])
screen['sedang'] = fuzz.trimf(screen_universe, [3, 5.5, 8])
screen['tinggi'] = fuzz.trimf(screen_universe, [7, 10, 12])

temp['dingin'] = fuzz.trimf(temp_universe, [10, 18, 22])
temp['nyaman'] = fuzz.trimf(temp_universe, [20, 24, 28])
temp['panas'] = fuzz.trimf(temp_universe, [26, 30, 40])

stress['rendah'] = fuzz.trimf(stress_universe, [0, 20, 40])
stress['sedang'] = fuzz.trimf(stress_universe, [30, 50, 70])
stress['tinggi'] = fuzz.trimf(stress_universe, [60, 80, 100])

humid['kering'] = fuzz.trimf(humid_universe, [0, 0, 35])
humid['ideal'] = fuzz.trimf(humid_universe, [25, 50, 75])
humid['lembab'] = fuzz.trimf(humid_universe, [65, 100, 100])

airq['buruk'] = fuzz.trimf(aq_universe, [0, 0, 40])
airq['sedang'] = fuzz.trimf(aq_universe, [30, 50, 70])
airq['baik'] = fuzz.trimf(aq_universe, [60, 100, 100])

# ====================================
# RULE BASE (Sama seperti yang Anda berikan)
# ====================================
rules = [
    # 9 ATURAN DASAR (Screen & Temp) - Jika lingkungan Ideal, stres normal
    ctrl.Rule(screen['rendah'] & temp['dingin'] & humid['ideal'] & airq['baik'], stress['rendah']),
    ctrl.Rule(screen['rendah'] & temp['nyaman'] & humid['ideal'] & airq['baik'], stress['rendah']),
    ctrl.Rule(screen['rendah'] & temp['panas'] & humid['ideal'] & airq['baik'], stress['sedang']),
    
    ctrl.Rule(screen['sedang'] & temp['dingin'] & humid['ideal'] & airq['baik'], stress['sedang']),
    ctrl.Rule(screen['sedang'] & temp['nyaman'] & humid['ideal'] & airq['baik'], stress['sedang']),
    ctrl.Rule(screen['sedang'] & temp['panas'] & humid['ideal'] & airq['baik'], stress['tinggi']),
    
    ctrl.Rule(screen['tinggi'] & temp['dingin'] & humid['ideal'] & airq['baik'], stress['tinggi']),
    ctrl.Rule(screen['tinggi'] & temp['nyaman'] & humid['ideal'] & airq['baik'], stress['tinggi']),
    ctrl.Rule(screen['tinggi'] & temp['panas'] & humid['ideal'] & airq['baik'], stress['tinggi']),
    
    # ATURAN PENALTI LINGKUNGAN (Memicu Stress Lebih Tinggi dari Kondisi Dasar)
    
    # Kualitas Udara Buruk
    ctrl.Rule(airq['buruk'], stress['tinggi']), # Jika AQ buruk, stress pasti tinggi
    
    # Kelembaban Ekstrim (Kering atau Lembab)
    ctrl.Rule(humid['kering'], stress['sedang']), 
    ctrl.Rule(humid['lembab'], stress['sedang']),
    
    # Kualitas Udara Sedang + Layar Sedang/Tinggi
    ctrl.Rule((screen['sedang'] | screen['tinggi']) & airq['sedang'], stress['tinggi'])
]

# Rule Base baru harus menggunakan semua Antecedent yang didefinisikan.
stress_ctrl = ctrl.ControlSystem(rules)
stress_sim = ctrl.ControlSystemSimulation(stress_ctrl)

# ====================================
# WRAPPER FUNCTION (Sudah Sinkron)
# ====================================

def calculate_stress(screentime, temperature, humidity, air_quality):
    """
    Menghitung tingkat stres menggunakan Logika Fuzzy berdasarkan 4 variabel:
    waktu layar, suhu, kelembaban, dan kualitas udara.
    """
    
    # Memastikan input sesuai dengan universe
    screentime = max(0, min(screentime, 12)) 
    temperature = max(10, min(temperature, 40)) 
    humidity = max(0, min(humidity, 100)) # Baru
    air_quality = max(0, min(air_quality, 100)) # Baru
    
    stress_sim.input['screen'] = screentime
    stress_sim.input['temperature'] = temperature
    stress_sim.input['humidity'] = humidity # Input Baru
    stress_sim.input['air_quality'] = air_quality # Input Baru

    try:
        stress_sim.compute()
        value = stress_sim.output['stress']
    except ValueError as e:
        print(f"Error komputasi fuzzy: {e}. Mengembalikan nilai default 50.")
        value = 50 

    category = (
        "Rendah" if value < 35 else
        "Sedang" if value < 65 else
        "Tinggi"
    )

    message = {
        "Rendah": "Kondisi kamu aman dan rileks 👍",
        "Sedang": "Mulai perhatikan kondisi tubuh dan waktu layar 😊",
        "Tinggi": "Tingkat stres tinggi! Kurangi layar dan istirahat 😣"
    }[category]

    return {
        "stress_value": float(value),
        "category": category,
        "message": message
    }

if __name__ == '__main__':
    # Contoh 1: Stress Tinggi karena Layar Tinggi dan Suhu Panas (seperti sebelumnya)
    contoh_data_1 = calculate_stress(7, 30, 50, 90) # AQ Baik, Humid Ideal
    print(f"Contoh 1 (Layar 7h, Suhu 30C, Humid 50%, AQ 90%): {contoh_data_1}") 
    
    # Contoh 2: Stress Naik karena AQ Buruk (Layar Rendah)
    contoh_data_2 = calculate_stress(2, 25, 50, 30) # Layar Rendah, AQ Buruk
    print(f"Contoh 2 (Layar 2h, Suhu 25C, Humid 50%, AQ 30%): {contoh_data_2}") 
    
    # Contoh 3: Stress Naik karena Kelembaban Ekstrim (Layar Rendah)
    contoh_data_3 = calculate_stress(2, 25, 90, 90) # Layar Rendah, Humid Lembab
    print(f"Contoh 3 (Layar 2h, Suhu 25C, Humid 90%, AQ 90%): {contoh_data_3}")