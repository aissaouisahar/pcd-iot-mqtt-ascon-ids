import pandas as pd
import numpy as np
import os
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score, precision_score
from imblearn.over_sampling import RandomOverSampler

# ── CONFIGURATION ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_PATH = os.path.join(BASE_DIR, "data", "train_cleaned.csv")

FEATURES = [
    "tcp.time_delta", "tcp.len", "mqtt.len", "mqtt.msgtype", 
    "msg_per_sec", "entropy", "payload_ratio", "interval_std", "burst_ratio"
]
TARGET = "target"

def validation_empirique():
    print("="*65)
    print("  PHASE DE VALIDATION EMPIRIQUE (RECHERCHE DES PARAMÈTRES)")
    print("="*65)
    
    # 1. Chargement d'un échantillon significatif (200 000 lignes)
    print(f"[i] Chargement de 200,000 messages pour tests rapides...")
    df = pd.read_csv(TRAIN_PATH, low_memory=False).dropna(subset=FEATURES + [TARGET])
    sample_df = df.sample(n=200000, random_state=42)

    # 2. Séparation Train / Validation interne (pour éviter le 100% de précision)
    # On apprend sur une partie du sample, on teste sur l'autre partie du sample
    train_val, test_val = train_test_split(sample_df, test_size=0.3, random_state=42)

    X_train = train_val[FEATURES].values
    X_test  = test_val[FEATURES].values
    y_test_bin = (test_val[TARGET] != "legitimate").astype(int)

    # Normalisation
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # Scénarios à tester
    scenarios = [
        {"name": "Mode Prudent",   "contam": 0.05, "seuil": 0.50},
        {"name": "Mode Équilibré", "contam": 0.15, "seuil": 0.80},
        {"name": "Mode Sécurisé",  "contam": 0.25, "seuil": 0.95}, # Votre choix final
    ]

    print(f"\n{'SCÉNARIO':<18} | {'CONTAM.':<8} | {'SEUIL':<8} | {'RECALL':<10} | {'PRÉCISION'}")
    print("-" * 65)

    for sc in scenarios:
        # A. Isolation Forest (entraîné sur legitimate uniquement dans le train_val)
        X_train_legit = train_val[train_val[TARGET] == "legitimate"][FEATURES].values
        X_train_legit_scaled = scaler.transform(X_train_legit)
        
        model_if = IsolationForest(n_estimators=100, contamination=sc['contam'], random_state=42, n_jobs=-1)
        model_if.fit(X_train_legit_scaled)
        
        # B. Random Forest (sur tout le train_val avec rééquilibrage)
        ros = RandomOverSampler(random_state=42)
        X_res, y_res = ros.fit_resample(X_train, train_val[TARGET])
        
        model_rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        model_rf.fit(X_res, y_res)

        # C. Évaluation sur test_val (Données inconnues du modèle)
        # 1. Filtre IF
        is_anomaly_if = (model_if.predict(X_test_scaled) == -1)
        
        # 2. Raffinement RF avec Seuil
        pred_bin = np.zeros(len(test_val))
        if is_anomaly_if.sum() > 0:
            probs = model_rf.predict_proba(X_test[is_anomaly_if])
            classes = model_rf.classes_.tolist()
            idx_legit = classes.index("legitimate")
            
            final_preds = []
            for p in probs:
                # Si proba d'attaque (1 - proba legit) > Seuil
                if (1 - p[idx_legit]) >= (1 - sc['seuil']): 
                    final_preds.append(1)
                else:
                    final_preds.append(0)
            pred_bin[is_anomaly_if] = final_preds

        # Calcul des scores
        rec = recall_score(y_test_bin, pred_bin, zero_division=0)
        prec = precision_score(y_test_bin, pred_bin, zero_division=0)
        
        print(f"{sc['name']:<18} | {sc['contam']:<8.2f} | {sc['seuil']:<8.2f} | {rec:>9.2%} | {prec:>9.2%}")

    print("-" * 65)
    print("[i] Validation terminée. Utilisez ces chiffres pour justifier vos choix.")

if __name__ == "__main__":
    validation_empirique()