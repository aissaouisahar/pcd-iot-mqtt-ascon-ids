import os
import numpy as np
import pandas as pd
import math

# -- Chemins --
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_PATH = os.path.join(BASE_DIR, "data", "train70.csv")
TEST_PATH = os.path.join(BASE_DIR, "data", "test30.csv")
TRAIN_CLEAN = os.path.join(BASE_DIR, "data", "train_cleaned.csv")
TEST_CLEAN = os.path.join(BASE_DIR, "data", "test_cleaned.csv")

TARGET = "target"
FEATURES_RAW = ["tcp.time_delta", "tcp.len", "mqtt.len", "mqtt.msgtype", "mqtt.hdrflags"]

def shannon_entropy_proxy(row):
    """
    Simule l'entropie de Shannon pour le CSV. 
    On utilise mqtt.len et hdrflags pour recréer une variabilité mathématique.
    """
    m_len = float(row['mqtt.len'])
    flags = float(row['mqtt.hdrflags'])
    if m_len <= 0: return 0.0
    # On simule la complexité : un mélange entre la taille et les flags
    p1 = (flags + 1) / (m_len + 2)
    p2 = 1 - p1
    if p1 <= 0 or p2 <= 0: return 0.0
    return - (p1 * math.log2(p1) + p2 * math.log2(p2))

def feature_engineering(df):
    print("\n  [3] Feature Engineering (Synchronisation Temps Réel)...")
    
    # 1. tcp.len harmonisé (On utilise l'estimation du temps réel)
    df["tcp.len"] = df["mqtt.len"].astype(float) + 52
    
    # 2. msg_per_sec (Moyenne glissante sur 5 messages pour simuler les 5 sec)
    df["msg_per_sec"] = 1.0 / (df["tcp.time_delta"].rolling(window=5).mean() + 0.0001)
    
    # 3. entropy (Vraie simulation de Shannon)
    df["entropy"] = df.apply(shannon_entropy_proxy, axis=1)
    
    # 4. payload_ratio
    df["payload_ratio"] = df["mqtt.len"].astype(float) / (df["tcp.len"] + 1e-6)
    
    # 5. interval_std
    df["interval_std"] = df["tcp.time_delta"].rolling(window=5).std()
    
    # 6. burst_ratio
    df["burst_ratio"] = (df["tcp.time_delta"] < 0.1).astype(int)
    
    return df.fillna(0)

def nettoyer_dataset(df):
    # Nettoyage de base
    for col in FEATURES_RAW:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df = df.dropna(subset=[TARGET])
    df = feature_engineering(df)
    
    # Garder uniquement l'ordre exact utilisé par le modèle
    FINAL_COLS = ["tcp.time_delta", "tcp.len", "mqtt.len", "mqtt.msgtype", 
                  "msg_per_sec", "entropy", "payload_ratio", "interval_std", "burst_ratio", TARGET]
    return df[FINAL_COLS]

if __name__ == "__main__":
    print("[i] Chargement et synchronisation des données...")
    train = pd.read_csv(TRAIN_PATH, low_memory=False)
    test = pd.read_csv(TEST_PATH, low_memory=False)
    
    nettoyer_dataset(train).to_csv(TRAIN_CLEAN, index=False)
    nettoyer_dataset(test).to_csv(TEST_CLEAN, index=False)
    print("[✓] Fichiers _cleaned synchronisés avec le temps réel.")