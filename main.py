import machine
import utime
import dht
import network
import urequests
import _thread
from imu import MPU6050

# --- CONFIGURATION ---
WEB_URL = "https://your-ngrok-url.ngrok-free.app/alert" # UPDATE THIS!
CRASH_THRESHOLD = 3.5  # G-Force
SMOKE_THRESHOLD = 35000 
SEND_INTERVAL = 5      # Seconds between normal updates

# --- HARDWARE SETUP ---
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1))
imu = MPU6050(i2c)
dht_sensor = dht.DHT22(machine.Pin(15))
gas_sensor = machine.ADC(26)
wdt = machine.WDT(timeout=8000) # Safety Rebooter

# Global variables for Core-to-Core communication
telemetry = {"speed": 0, "impact": 1.0, "gas": 0, "temp": 0, "hum": 0, "emergency": False}
new_data_ready = False

def network_thread():
    """CORE 1: Dedicated to Wi-Fi and Web Requests"""
    global new_data_ready
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Wokwi-GUEST", "")
    
    while not wlan.isconnected():
        utime.sleep(1)
    
    print("Network Active:", wlan.ifconfig()[0])
    
    while True:
        if new_data_ready:
            try:
                # Send the global telemetry dictionary as JSON
                res = urequests.post(WEB_URL, json=telemetry)
                res.close()
                new_data_ready = False 
            except:
                print("Web Error")
        utime.sleep(0.1)

# Start Network Thread on Core 1
_thread.start_new_thread(network_thread, ())

# --- MAIN LOOP (CORE 0) ---
velocity = 0.0
last_t = utime.ticks_ms()
last_send = 0

while True:
    wdt.feed()
    try:
        # 1. Physics & Timing
        dt = (utime.ticks_ms() - last_t) / 1000.0
        last_t = utime.ticks_ms()
        
        # 2. Sensor Readings
        dht_sensor.measure()
        accel = imu.accel
        gas_val = gas_sensor.read_u16()
        
        # 3. Refined Speed Math (X-axis only)
        ax = accel.x if abs(accel.x) > 0.05 else 0
        velocity += (ax * 9.81) * dt
        velocity = max(0, velocity * 0.98) # Friction/Damping
        
        g_force = (accel.x**2 + accel.y**2 + accel.z**2)**0.5
        is_emergency = g_force > CRASH_THRESHOLD or gas_val > SMOKE_THRESHOLD

        # 4. Prepare Data for Core 1
        if is_emergency or (utime.time() - last_send >= SEND_INTERVAL):
            telemetry.update({
                "speed": velocity * 3.6, # km/h
                "impact": g_force,
                "gas": gas_val,
                "temp": dht_sensor.temperature(),
                "hum": dht_sensor.humidity(),
                "emergency": is_emergency
            })
            new_data_ready = True
            last_send = utime.time()
            if is_emergency: print("!!! CRASH ALERT !!!")

        utime.sleep(0.1)
    except Exception as e:
        print("Sensor Error:", e)