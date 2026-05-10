
#!/usr/bin/env python3

 
import paho.mqtt.client as mqtt
import base64
import json
import time
import sys
import os
 
# ============================================================
# CHARGEMENT DE ASCON — VERSION CORRIGÉE
# ============================================================
# IMPORTANT : on charge ascon.py depuis le MEME dossier que ce script,
# PAS depuis pyascon-master qui peut contenir une vieille version
# pré-NIST (incompatible avec ascon.h sur l'ESP32).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
 
from ascon import ascon_encrypt, ascon_decrypt
 
# ============================================================
# CONFIGURATION
# ============================================================
BROKER_IP   = "10.43.209.150"  
BROKER_PORT = 1883
TOPIC_SUB   = "iot/sensor/ecg"
 
# Clé partagée avec l'ESP32 — DOIT être identique
ASCON_KEY = bytes([
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F
])
 
# Données associées — DOIT être identique à l'ESP32 (8 octets, sans \0 final)
ASSOCIATED_DATA = b"ENSI_IOT"
 
 

 
KAT_KEY   = bytes(range(16))
KAT_NONCE = bytes(range(16))
KAT_AD    = b""
KAT_PT    = b""
KAT_TAG_EXPECTED = bytes.fromhex("d4d2257f60f7996b039b893be6d90f9e")
 
 
def check_ascon_version():
    """
    Vérifie que la version de ascon.py chargée est bien la version NIST SP 800-232.
    Si ce test échoue → il y a une vieille version de ascon.py quelque part dans
    le sys.path qui est chargée à la place.
    """
    print("[KAT] Vérification de la version ASCON chargée...")
    try:
        ct_tag = ascon_encrypt(KAT_KEY, KAT_NONCE, KAT_AD, KAT_PT)
    except Exception as e:
        print(f"[KAT]  ECHEC : impossible d'appeler ascon_encrypt : {e}")
        print("[KAT]    => La version de ascon.py chargée n'a pas la bonne API.")
        return False
 
    # ct_tag doit être uniquement le tag (16 octets) puisque PT est vide
    if len(ct_tag) != 16:
        print(f"[KAT]  ECHEC : taille inattendue ({len(ct_tag)} au lieu de 16)")
        return False
 
    if ct_tag != KAT_TAG_EXPECTED:
        print(f"[KAT] ECHEC : tag calculé    = {ct_tag.hex()}")
        print(f"[KAT]            tag attendu    = {KAT_TAG_EXPECTED.hex()}")
        print(f"[KAT]    => La version de ascon.py chargée n'est PAS conforme NIST SP 800-232.")
        print(f"[KAT]    => Vérifier le chemin :  {ascon_encrypt.__module__}")
        try:
            import ascon as _a
            print(f"[KAT]    => Fichier chargé    :  {_a.__file__}")
        except Exception:
            pass
        return False
 
    print(f"[KAT] OK — tag {ct_tag.hex()} conforme NIST SP 800-232")
    return True
 
 
# ============================================================
# DÉCHIFFREMENT ASCON
# ============================================================
 
def decrypt_payload(b64_payload: str) -> dict | None:
    """
    Reçoit un payload Base64 de l'ESP32.
    Format : base64(nonce[16] || ciphertext[n] || tag[16])
    Retourne le JSON déchiffré ou None si échec.
    """
    try:
        raw = base64.b64decode(b64_payload)
        if len(raw) < 16 + 16:
            print("[ASCON] Payload trop court")
            return None
 
        nonce      = raw[:16]
        ciphertext = raw[16:]   # inclut le tag 16 octets à la fin
 
        t0 = time.perf_counter()
        plaintext = ascon_decrypt(
            key            = ASCON_KEY,
            nonce          = nonce,
            associateddata = ASSOCIATED_DATA,
            ciphertext     = ciphertext,
            variant        = "Ascon-AEAD128"
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"[ASCON] Déchiffrement: {elapsed_ms:.3f} ms")
 
        if plaintext is None:
            print("[ASCON] Authentification échouée — message corrompu ou attaque")
            print(f"[DEBUG] Nonce reçu        : {nonce.hex()}")
            print(f"[DEBUG] CT+tag reçu       : {ciphertext.hex()}")
            print(f"[DEBUG] Tag reçu          : {ciphertext[-16:].hex()}")
            print(f"[DEBUG] Clé utilisée      : {ASCON_KEY.hex()}")
            print(f"[DEBUG] AD utilisée       : {ASSOCIATED_DATA.hex()} ({ASSOCIATED_DATA!r})")
            return None
 
        data = json.loads(plaintext.decode("utf-8"))
        return data
 
    except Exception as e:
        print(f"[ASCON] Erreur déchiffrement: {e}")
        import traceback
        traceback.print_exc()
        return None
 
 
# ============================================================
# CALLBACKS MQTT
# ============================================================
 
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MQTT] Connecté au broker {BROKER_IP}:{BROKER_PORT}")
        client.subscribe(TOPIC_SUB)
        print(f"[MQTT] Abonné à: {TOPIC_SUB}")
    else:
        print(f"[MQTT] Échec connexion, code: {reason_code}")
 
 
def on_message(client, userdata, msg):
    print("\n" + "─" * 55)
    print(f"[MQTT] Topic   : {msg.topic}")
 
    b64_payload = msg.payload.decode("utf-8", errors="ignore")
    print(f"[MQTT] Payload B64 : {b64_payload[:60]}{'...' if len(b64_payload) > 60 else ''}")
 
    data = decrypt_payload(b64_payload)
    if data is not None:
        print(f"[DATA] Plaintext déchiffré:")
        print(f"       ID     : {data.get('id')}")
        print(f"       ECG    : {data.get('ecg')}")
        print(f"       BPM    : {data.get('bpm')} bpm")
        print(f"       IP ESP : {data.get('ip')}")
        print(f"       RSSI   : {data.get('rssi')} dBm")
        # ─── ICI : brancher le module IDS ──────────────────────
        # ids_predict(data)  # à activer quand ids_model.pkl prêt
    else:
        print("[DATA] Impossible de déchiffrer le message")
    print("─" * 55)
 
 
def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT] Déconnecté (code: {reason_code}) — reconnexion en cours...")
 
 
# ============================================================
# MAIN
# ============================================================
 
def main():
    print("=" * 55)
    print("  Subscriber MQTT + ASCON-AEAD128")
    print("=" * 55)
 
    # 1. Vérifier la version d'ASCON AVANT de se connecter au broker
    if not check_ascon_version():
        print("\n[FATAL] La version de ascon.py n'est pas compatible NIST SP 800-232.")
        print("        Le déchiffrement échouera systématiquement.")
        print("        => Remplacez ascon.py par la version NIST officielle :")
        print("           https://github.com/meichlseder/pyascon")
        print("        => Ou supprimez le dossier pyascon-master qui interfère.")
        sys.exit(1)
 
    # 2. Afficher les paramètres
    print(f"\n[CONFIG] Clé ASCON (hex) : {ASCON_KEY.hex()}")
    print(f"[CONFIG] AD              : {ASSOCIATED_DATA!r} ({ASSOCIATED_DATA.hex()})")
 
    # 3. Test crypto local (chiffrement → déchiffrement) pour validation finale
    print("\n[TEST] Round-trip chiffrement/déchiffrement local...")
    test_nonce = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    test_pt    = b'{"id":1,"ecg":2048,"bpm":75,"ip":"10.43.209.150","rssi":-60}'
    test_ct    = ascon_encrypt(ASCON_KEY, test_nonce, ASSOCIATED_DATA, test_pt)
    test_dec   = ascon_decrypt(ASCON_KEY, test_nonce, ASSOCIATED_DATA, test_ct)
    if test_dec == test_pt:
        print("[TEST]  Round-trip OK")
    else:
        print("[TEST]  Round-trip ECHEC (improbable si KAT a passé) !")
        sys.exit(1)
 
    # 4. Connexion au broker
    print()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect
 
    try:
        client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Arrêt du subscriber.")
        client.disconnect()
 
 
if __name__ == "__main__":
    main()

