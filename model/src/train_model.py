"""
TRAIN_HYBRID.PY - VERSION FINALE (OPTIMISÉE JURY)
-----------------------------------------------
Architecture : Isolation Forest (Filtre) + Random Forest (Classifieur)
"""

import os
import numpy as np
import pandas as pd
import joblib
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix
)

# ── 1. CONFIGURATION DES CHEMINS ─────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_PATH   = os.path.join(BASE_DIR, "data", "train_cleaned.csv")
TEST_PATH    = os.path.join(BASE_DIR, "data", "test_cleaned.csv")
IF_PATH      = os.path.join(BASE_DIR, "models", "if_model.pkl")
RF_PATH      = os.path.join(BASE_DIR, "models", "rf_model.pkl")
SCALER_PATH  = os.path.join(BASE_DIR, "models", "scaler.pkl")

os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)

FEATURES = [
    "tcp.time_delta", "tcp.len", "mqtt.len", "mqtt.msgtype", 
    "msg_per_sec", "entropy", "payload_ratio", "interval_std", "burst_ratio"
]
TARGET = "target"

# ── 2. FONCTIONS DE CALCUL ET AFFICHAGE ──────────────────────────────────────
def evaluer_modele(y_reel, y_pred, titre):
    cm = confusion_matrix(y_reel, y_pred)
    acc = accuracy_score(y_reel, y_pred)
    prec = precision_score(y_reel, y_pred, zero_division=0)
    rec = recall_score(y_reel, y_pred, zero_division=0)
    f1 = f1_score(y_reel, y_pred, zero_division=0)
    
    print(f"\n" + "─"*50)
    print(f"  RÉSULTATS : {titre}")
    print(f"  " + "─"*50)
    print(f"  Matrice de Confusion (Réel vs Prédit) :")
    print(f"  {'':25} {'Prédit Normal':>15} {'Prédit Anomalie':>16}")
    print(f"  {'Réel Normal':25} {cm[0][0]:>15}  {cm[0][1]:>15}")
    print(f"  {'Réel Anomalie':25} {cm[1][0]:>15}  {cm[1][1]:>15}")
    print(f"\n  Scores : Accuracy: {acc:.2%} | Précision: {prec:.2%} | Rappel: {rec:.2%} | F1: {f1:.2%}")
    
    return {"acc": acc, "prec": prec, "rec": rec, "f1": f1, "fp": cm[0][1], "fn": cm[1][0]}

# ── 3. CHARGEMENT DES DONNÉES ────────────────────────────────────────────────
def charger_donnees():
    print("=" * 60 + "\n  IDS MQTT — ÉVALUATION DU MODÈLE HYBRIDE\n" + "=" * 60)
    train = pd.read_csv(TRAIN_PATH, low_memory=False).dropna(subset=FEATURES + [TARGET])
    test  = pd.read_csv(TEST_PATH, low_memory=False).dropna(subset=FEATURES + [TARGET])
    print(f"[i] Jeu d'entraînement : {len(train)} messages")
    print(f"[i] Jeu de test         : {len(test)} messages")
    return train, test

# ── 4. ÉTAPE 1 : ISOLATION FOREST ────────────────────────────────────────────
def etape1_isolation_forest(train, test):
    print("\n" + "=" * 60 + "\n  ÉTAPE 1 — FILTRAGE PAR ISOLATION FOREST\n" + "=" * 60)
    X_train_if = train[train[TARGET] == "legitimate"][FEATURES].values
    X_test_all = test[FEATURES].values
    y_test_binary = (test[TARGET] != "legitimate").astype(int)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_if)
    X_test_scaled  = scaler.transform(X_test_all)

    model_if = IsolationForest(n_estimators=300, contamination=0.25, random_state=42, n_jobs=-1)
    model_if.fit(X_train_scaled)

    pred_test = (model_if.predict(X_test_scaled) == -1).astype(int)
    metrics_if = evaluer_modele(y_test_binary, pred_test, "ISOLATION FOREST (TEST)")

    joblib.dump(model_if, IF_PATH)
    joblib.dump(scaler, SCALER_PATH)
    # --- ÉVALUATION SUR L'ENTRAÎNEMENT ---
    X_train_all = train[FEATURES].values
    y_train_bin = (train[TARGET] != "legitimate").astype(int)
    pred_train = (model_if.predict(scaler.transform(X_train_all)) == -1).astype(int)
    evaluer_modele(y_train_bin, pred_train, "IF - ENTRAÎNEMENT (Auto-évaluation)")

    # --- ÉVALUATION SUR LE TEST ---
    X_test_all = test[FEATURES].values
    y_test_bin = (test[TARGET] != "legitimate").astype(int)
    pred_test = (model_if.predict(scaler.transform(X_test_all)) == -1).astype(int)
    metrics_if = evaluer_modele(y_test_bin, pred_test, "IF - TEST (Généralisation)")
    return model_if, scaler, metrics_if

# ── 5. ÉTAPE 2 : RANDOM FOREST ───────────────────────────────────────────────
def etape2_random_forest(train, test):
    print("\n" + "=" * 60 + "\n  ÉTAPE 2 — CLASSIFICATION PAR RANDOM FOREST (SMOTE)\n" + "=" * 60)
    
    X_train = train[FEATURES].values
    y_train = train[TARGET].values

    # 1. Sous-échantillonnage (UnderSampling) pour réduire la classe majoritaire
    print(f"[i] Réduction de la classe 'legitimate'...")
    rus = RandomUnderSampler(sampling_strategy={'legitimate': 800000}, random_state=42)
    X_mid, y_mid = rus.fit_resample(X_train, y_train)

    # 2. SMOTE (OverSampling) pour créer des données synthétiques
    from imblearn.over_sampling import SMOTE
    print(f"[i] Création de données synthétiques avec SMOTE...")
    smote = SMOTE(sampling_strategy={
        'flood': 15000, 
        'malformed': 15000, 
        'slowite': 15000
    }, random_state=42)
    
    # ON UTILISE LES NOMS X_res et y_res ICI
    X_res, y_res = smote.fit_resample(X_mid, y_mid)
    
    print(f"    Taille finale après SMOTE : {len(X_res)} échantillons")

    # 3. Entraînement
    model_rf = RandomForestClassifier(n_estimators=300, max_depth=20, class_weight="balanced", random_state=42, n_jobs=-1)
    
    # VÉRIFIEZ BIEN QUE LES NOMS CORRESPONDENT ICI :
    model_rf.fit(X_res, y_res)

    print("\n[i] Rapport détaillé (RF seul) :")
    pred_rf = model_rf.predict(test[FEATURES].values)
    print(classification_report(test[TARGET], pred_rf, zero_division=0))

    joblib.dump(model_rf, RF_PATH)
    return model_rf

# ── 6. ÉTAPE 3 : PIPELINE FINAL ──────────────────────────────────────────────
def etape3_pipeline_final(test, model_if, model_rf, scaler):
    print("\n" + "=" * 60 + "\n  ÉTAPE 3 — PIPELINE HYBRIDE (DÉCISION FINALE)\n" + "=" * 60)
    X_test = test[FEATURES].values
    y_test_binary = (test[TARGET] != "legitimate").astype(int)
    classes_rf = model_rf.classes_.tolist()
    idx_legit = classes_rf.index("legitimate")

    X_scaled = scaler.transform(X_test)
    is_anomaly = (model_if.predict(X_scaled) == -1)

    pred_final = np.where(~is_anomaly, "legitimate", "unknown")
    if is_anomaly.sum() > 0:
        probs_rf = model_rf.predict_proba(X_test[is_anomaly])
        predictions = []
        for p in probs_rf:
            if p[idx_legit] < 0.05: # Seuil attaque > 70%
                best_attack_idx = np.argmax(np.delete(p, idx_legit))
                attack_classes = [c for c in classes_rf if c != "legitimate"]
                predictions.append(attack_classes[best_attack_idx])
            else:
                predictions.append("legitimate")
        pred_final[is_anomaly] = predictions

    y_pred_binary = (pred_final != "legitimate").astype(int)
    metrics_final = evaluer_modele(y_test_binary, y_pred_binary, "ARCHITECTURE HYBRIDE FINALE")
    return metrics_final

# ── 7. RÉSUMÉ JURY ───────────────────────────────────────────────────────────
def afficher_resume_jury(m_if, m_final):
    print("\n" + "═"*65 + "\n  SYNTHÈSE POUR LA PRÉSENTATION JURY\n" + "═"*65)
    print(f"  {'MODÈLE':<25} | {'RAPPEL (DÉTECTION)':<20} | {'FAUSSES ALERTES'}")
    print(f"  " + "-"*62)
    print(f"  {'Isolation Forest (Seul)':<25} | {m_if['rec']:>18.2%} | {m_if['fp']}")
    print(f"  {'Architecture Hybride':<25} | {m_final['rec']:>18.2%} | {m_final['fp']}")
    reduction = (m_if['fp'] - m_final['fp']) / m_if['fp'] if m_if['fp'] > 0 else 0
    print(f"  " + "-"*62)
    print(f"  [Conclusion] L'hybridation a réduit les fausses alertes de {reduction:.1%}.")
    print("═"*65)

if __name__ == "__main__":
    train_df, test_df = charger_donnees()
    m_if, scaler, metrics_if = etape1_isolation_forest(train_df, test_df)
    m_rf = etape2_random_forest(train_df, test_df)
    # Appel corrigé ici
    metrics_final = etape3_pipeline_final(test_df, m_if, m_rf, scaler)
    afficher_resume_jury(metrics_if, metrics_final)