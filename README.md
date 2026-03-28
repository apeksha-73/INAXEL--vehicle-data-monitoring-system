# 🚗INAXEL-Vehicle Data monitorning System

A Raspberry Pi Pico W based system for real-time vehicle monitoring, 
crash detection, and cloud-based alerting.

## 🛠️ Hardware Components
* **Microcontroller:** Raspberry Pi Pico W
* **Sensors:** MPU6050 (Accel/Gyro), DHT22 (Temp/Hum), MQ-2 (Smoke)
* **Storage:** Internal Flash (Black Box Logging)

## 🚀 Features
- **Accident Detection:** Uses G-force resultant vector analysis.
- **Fire Monitoring:** Analog smoke detection.
- **Cloud Dashboard:** Live telemetry sent via Flask & Ngrok.
- **Dual-Core Processing:** Sensor logic runs independently of Wi-Fi.

## ⚙️ Setup Instructions
1. Upload `main.py` to the Pico W.
2. Run `app.py` in VS Code to start the Flask server.
3. Use `ngrok http 5000` to create a public tunnel.
4. Update the `WEB_URL` in `main.py` with your Ngrok link.
