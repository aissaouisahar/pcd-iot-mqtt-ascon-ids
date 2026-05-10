#!/usr/bin/env python3

 
import os
import logging
import joblib
import numpy as np
import base64
import time
import math
from collections import deque
import paho.mqtt.client as mqtt
 
# Détection version paho-mqtt
try:
    from paho.mqtt.client import CallbackAPIVersion
    PAHO_VERSION = 2
except ImportError:
    PAHO_VERSION = 1
 
# ═══════════════════════════════════════════════════════════
# CHEMINS
# ═══════════════════════════════════════════════════════════
 
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR     = os.path.join(BASE_DIR, "models")
IF_MODEL_PATH  = os.path.join(MODELS_DIR, "if_model.pkl")
RF_MODEL_PATH  = os.path.join(MODELS_DIR, "rf_model.pkl")
SCALER_PATH    = os.path.join(MODELS_DIR, "scaler.pkl")
LOG_PATH       = os.path.join(BASE_DIR, "logs", "alerts.log")
 
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
 
# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════
 
BROKER_HOST    = "10.43.209.150" 
""  
BROKER_PORT    = 1883
 
TOPIC_INPUT    = "iot/sensor/ecg/raw"
TOPIC_OUTPUT   = "iot/sensor/ecg"
TOPIC_ALERT    = "iot/ids/alerts"
 
MQTT_HDRFLAGS = 48  
 

 

SEUIL_LEGITIME = 0.20 
 

USE_ISOLATION_FOREST = False  
 

SEUIL_ATTAQUE_FORTE = 0.50  
 

 
RED, GREEN, YELLOW, RESET = "\033[91m", "\033[92m", "\033[93m", "\033[0m"
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IDS-MQTT-ECG")
 

 
class FeatureExtractorECG:
    def __init__(self, window_sec: float = 5.0):
        self.window_sec = window_sec
        self.timestamps = deque()
        self.intervals  = deque(maxlen=20)
        self.last_time  = time.time()
    
    def _shannon_entropy_proxy(self, mqtt_len, mqtt_hdrflags):
        if mqtt_len <= 0:
            return 0.0
        p1 = (mqtt_hdrflags + 1) / (mqtt_len + 2)
        p2 = 1 - p1
        if p1 <= 0 or p2 <= 0:
            return 0.0
        return - (p1 * math.log2(p1) + p2 * math.log2(p2))
    
    def _purge_old_data(self, now):
        cutoff = now - self.window_sec
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()
    
    def extract(self, payload_b64):
        now = time.time()
        
        try:
            if isinstance(payload_b64, bytes):
                payload_b64 = payload_b64.decode('utf-8')
            full_packet = base64.b64decode(payload_b64)
        except:
            return [0.0] * 9
        
        time_delta = now - self.last_time
        self.last_time = now
        
        self.timestamps.append(now)
        self._purge_old_data(now)
        self.intervals.append(time_delta)
        
        mqtt_len = len(full_packet)
        tcp_len  = mqtt_len + 52
        mqtt_msgtype = 3
        msg_per_sec = len(self.timestamps) / self.window_sec if self.window_sec > 0 else 0.0
        entropy = self._shannon_entropy_proxy(mqtt_len, MQTT_HDRFLAGS)
        payload_ratio = mqtt_len / (tcp_len + 1e-6)
        
        if len(self.intervals) > 1:
            mean = sum(self.intervals) / len(self.intervals)
            interval_std = math.sqrt(
                sum((x - mean)**2 for x in self.intervals) / len(self.intervals)
            )
        else:
            interval_std = 0.0
        
        burst_count = sum(1 for i in self.intervals if i < 0.1)
        burst_ratio = burst_count / len(self.intervals) if self.intervals else 0.0
        
        return [
            float(time_delta),
            float(tcp_len),
            float(mqtt_len),
            float(mqtt_msgtype),
            float(msg_per_sec),
            float(entropy),
            float(payload_ratio),
            float(interval_std),
            float(burst_ratio)
        ]
 

 
def load_models():
    try:
        if_model = joblib.load(IF_MODEL_PATH)
        rf_model = joblib.load(RF_MODEL_PATH)
        scaler   = joblib.load(SCALER_PATH)
        logger.info(f"{GREEN}[ML]  Modèles chargés{RESET}")
        return if_model, rf_model, scaler, True
    except Exception as e:
        logger.error(f"{RED}[ML]  Erreur : {e}{RESET}")
        return None, None, None, False
 
extractor = FeatureExtractorECG(window_sec=5.0)
if_model, rf_model, scaler, MODELS_LOADED = load_models()
stats = {"total": 0, "allowed": 0, "blocked": 0, "attacks": {}}
 

 
def detect_attack(features):
   
    if not MODELS_LOADED:
        return False, "legitimate", 1.0, {}
    
    try:
        feat_array = np.array([features])
        feat_scaled = scaler.transform(feat_array)
        
       
        probs = rf_model.predict_proba(feat_array)[0]
        classes = rf_model.classes_.tolist()
        
      
        proba_dict = {classes[i]: probs[i] for i in range(len(classes))}
        
      
        prob_legit = proba_dict.get("legitimate", 0.0)
        
  
        attack_classes = [c for c in classes if c != "legitimate"]
        attack_probs = [proba_dict[c] for c in attack_classes]
        max_attack_prob = max(attack_probs) if attack_probs else 0.0
        max_attack_class = attack_classes[np.argmax(attack_probs)] if attack_probs else "unknown"
        
       
        
        
        if max_attack_prob >= SEUIL_ATTAQUE_FORTE:
            return True, max_attack_class, max_attack_prob, proba_dict
        

        if prob_legit >= SEUIL_LEGITIME:
            return False, "legitimate", prob_legit, proba_dict
        
      
        if USE_ISOLATION_FOREST:
            if_pred = if_model.predict(feat_scaled)[0]
            if if_pred == -1 and max_attack_prob >= 0.30:
                return True, max_attack_class, max_attack_prob, proba_dict
        
  
        return False, "legitimate", prob_legit, proba_dict
    
    except Exception as e:
        logger.error(f"{RED}[ML] Erreur détection : {e}{RESET}")
        return False, "legitimate", 0.0, {}
 

 
def on_message(client, userdata, msg):
    global stats
    stats["total"] += 1
    
    try:
        payload = msg.payload
        features = extractor.extract(payload)
        
       
        if stats["total"] <= 3:
            logger.info(f"{YELLOW}[DEBUG] Msg #{stats['total']}:{RESET}")
            logger.info(f"  msg_per_sec={features[4]:.2f}, entropy={features[5]:.3f}")
        
      
        is_attack, decision, confidence, probs = detect_attack(features)
        
        if is_attack:
            stats["blocked"] += 1
            stats["attacks"][decision] = stats["attacks"].get(decision, 0) + 1
            
            alert_msg = f"Attaque {decision.upper()} (msg #{stats['total']}, conf={confidence*100:.0f}%)"
            client.publish(TOPIC_ALERT, alert_msg)
            
            logger.warning(f"{RED}[BLOCK] Msg #{stats['total']} - Attaque {decision.upper()} ({confidence*100:.0f}%){RESET}")
        else:
            stats["allowed"] += 1
            client.publish(TOPIC_OUTPUT, payload)
            
            logger.info(f"{GREEN}[ALLOW] Msg #{stats['total']} → {TOPIC_OUTPUT} (legit={confidence*100:.0f}%){RESET}")
        
        
        if stats["total"] % 20 == 0:
            allow_pct = stats["allowed"] / stats["total"] * 100
            block_pct = stats["blocked"] / stats["total"] * 100
            logger.info(f"{YELLOW}[STATS] Total={stats['total']} | Allow={stats['allowed']} ({allow_pct:.0f}%) | Block={stats['blocked']} ({block_pct:.0f}%){RESET}")
    
    except Exception as e:
        logger.error(f"{RED}[ERREUR] {e}{RESET}")
        import traceback
        traceback.print_exc()
 

 
if PAHO_VERSION == 2:
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info(f"{GREEN}[MQTT]  Connecté{RESET}")
            client.subscribe(TOPIC_INPUT)
            logger.info(f"{GREEN}[MQTT]    {TOPIC_INPUT} → {TOPIC_OUTPUT}{RESET}")
    
    def on_disconnect(client, userdata, flags, reason_code, properties):
        logger.warning(f"{YELLOW}[MQTT] Déconnecté{RESET}")
else:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"{GREEN}[MQTT]  Connecté{RESET}")
            client.subscribe(TOPIC_INPUT)
            logger.info(f"{GREEN}[MQTT]    {TOPIC_INPUT} → {TOPIC_OUTPUT}{RESET}")
    
    def on_disconnect(client, userdata, rc):
        logger.warning(f"{YELLOW}[MQTT] Déconnecté{RESET}")
 

 
def main():
    logger.info("=" * 70)
    logger.info("  IDS MQTT ")
    logger.info("=" * 70)
    logger.info(f"[CONFIG] Broker         : {BROKER_HOST}:{BROKER_PORT}")

    
    if PAHO_VERSION == 2:
        client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="IDS_ECG")
    else:
        client = mqtt.Client(client_id="IDS_ECG")
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        logger.info(f"{GREEN}[IDS] Gateway actif{RESET}")
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info(f"\n{YELLOW}[IDS] Arrêt{RESET}")
    finally:
        logger.info("=" * 70)
        logger.info(f"  STATISTIQUES FINALES")
        logger.info("=" * 70)
        logger.info(f"  Total    : {stats['total']}")
        logger.info(f"  Allow    : {stats['allowed']}")
        logger.info(f"  Block    : {stats['blocked']}")
        if stats["attacks"]:
            logger.info(f"  Attaques détectées :")
            for att, cnt in stats["attacks"].items():
                logger.info(f"    - {att}: {cnt}")
        logger.info("=" * 70)
        try:
            client.disconnect()
        except:
            pass
 
if __name__ == "__main__":
    main()
