import machine
import utime
import dht
import network
import urequests
import _thread

# --- INTEGRATED DRIVER (Fixes Import Error) ---
class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00') 

    def _read_word(self, reg):
        h = self.i2c.readfrom_mem(self.addr, reg, 1)[0]
        l = self.i2c.readfrom_mem(self.addr, reg + 1, 1)[0]
        val = (h << 8) | l
        return val if val < 32768 else val - 65536

    @property
    def accel(self):
        x = self._read_word(0x3B) / 16384.0
        y = self._read_word(0x3D) / 16384.0
        z = self._read_word(0x3F) / 16384.0
        return type('Data', (), {'x':x, 'y':y, 'z':z})

# --- CONFIGURATION ---
WEB_URL = "https://your-ngrok-url.ngrok-free.app/alert" # Update with your Ngrok link
CRASH_THRESHOLD = 3.5  
SMOKE_THRESHOLD = 35000 

# --- HARDWARE ---
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1))
imu = MPU6050(i2c)
dht_sensor = dht.DHT22(machine.Pin(15))
gas_sensor = machine.ADC(26)

# Shared Data
telemetry = {"speed": 0, "impact": 1.0, "gas": 0, "temp": 0, "hum": 0, "emergency": False}
new_data_ready = False

def network_thread():
    global new_data_ready
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Wokwi-GUEST", "")
    while not wlan.isconnected(): utime.sleep(1)
    
    while True:
        if new_data_ready:
            try:
                res = urequests.post(WEB_URL, json=telemetry)
                res.close()
                new_data_ready = False 
            except: pass
        utime.sleep(0.2)

_thread.start_new_thread(network_thread, ())

# --- MONITORING LOOP ---
velocity = 0.0
last_t = utime.ticks_ms()

while True:
    dt = (utime.ticks_ms() - last_t) / 1000.0
    last_t = utime.ticks_ms()
    
    dht_sensor.measure()
    accel = imu.accel
    gas_val = gas_sensor.read_u16()
    
    # Speed Calculation
    ax = accel.x if abs(accel.x) > 0.05 else 0
    velocity += (ax * 9.81) * dt
    velocity = max(0, velocity * 0.98) 
    
    # Crash Detection (Resultant Vector)
    g_force = (accel.x**2 + accel.y**2 + accel.z**2)**0.5
    
    if g_force > CRASH_THRESHOLD or gas_val > SMOKE_THRESHOLD:
        telemetry.update({
            "speed": velocity * 3.6, "impact": g_force, "gas": gas_val,
            "temp": dht_sensor.temperature(), "hum": dht_sensor.humidity(),
            "emergency": True
        })
        new_data_ready = True
        print("!!! ALERT SENT !!!")

    utime.sleep(0.1)