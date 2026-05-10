import ascon
import paho.mqtt.client as mqtt
import time
import os
import random

# ── CONFIGURATION ──────────────────────────────────────────────────────────────
MQTT_BROKER = "10.43.209.150"
MQTT_PORT   = 1883
ASCON_KEY = bytes([
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F
])


PATIENT_IDS = [1, 2]
INTERVAL    = 2   

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connecté au broker Mosquitto ({MQTT_BROKER}:{MQTT_PORT})")
    else:
        print(f" Échec connexion — code : {rc}")

def on_publish(client, userdata, mid, reason_code=None, properties=None):
    print(f"   └─ Confirmé par le broker (mid={mid})")

print("Initialisation du simulateur ESP32...")
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_publish = on_publish

try:
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
except Exception as e:
    print(f" Impossible de se connecter : {e}")
    exit(1)

client.loop_start()
time.sleep(1)

print(f"\nSimulation en cours — patients : {PATIENT_IDS} — Ctrl+C pour arrêter")
print("─" * 55)

try:
    counter = 0
    while True:
        for patient_id in PATIENT_IDS:
            counter += 1

          
            valeur_bpm = round(random.uniform(60.0, 100.0), 1)
            data_bytes = str(valeur_bpm).encode('utf-8')

            nonce      = os.urandom(16)
            ciphertext = ascon.encrypt(ASCON_KEY, nonce, b"", data_bytes, "Ascon-128")
            packet     = nonce + ciphertext

        
            topic  = f"safe_ECG/{patient_id}"
            client.publish(topic, packet)

            print(f"[{counter:04d}] patient={patient_id}  BPM={valeur_bpm}  "
                  f"paquet={len(packet)}o  → {topic}")

            time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\n Simulation arrêtée.")
finally:
    client.loop_stop()
    client.disconnect()
    print(" Déconnecté.")
