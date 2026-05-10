"""
data.py
-------
Chargement et dispatching basé sur train70.csv et test30.csv
Classes : legitimate, dos, bruteforce, malformed, slowite, flood
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# ── Chemins ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_PATH  = os.path.join(BASE_DIR, "data", "train70.csv")
TEST_PATH   = os.path.join(BASE_DIR, "data", "test30.csv")

# ── Features sélectionnées ───────────────────────────────────────────────────
FEATURES = [
    "tcp.len",
    "tcp.time_delta",
    "mqtt.len",
    "mqtt.msgtype",
    "mqtt.qos",
    "mqtt.hdrflags",
    "mqtt.dupflag",
    "mqtt.retain",
]

LABEL_COL = "target"
CLASSES   = ["legitimate", "dos", "bruteforce", "malformed", "slowite", "flood"]


def _nettoyer(df: pd.DataFrame) -> pd.DataFrame:
    """Garde les colonnes utiles, remplace les NaN par la médiane."""
    df = df[df[LABEL_COL].isin(CLASSES)].copy()
    for col in FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())
    df = df[FEATURES + [LABEL_COL]].dropna()
    return df.reset_index(drop=True)


def charger_dataset():
    """Charge train70.csv et test30.csv et retourne les DataFrames nettoyés."""
    for path in [TRAIN_PATH, TEST_PATH]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Fichier introuvable : {path}\n"
                "Vérifiez que train70.csv et test30.csv sont dans le dossier data/"
            )

    print("[i] Chargement de train70.csv ...")
    df_train = pd.read_csv(TRAIN_PATH, low_memory=False)
    print(f"    -> {len(df_train)} lignes chargées")

    print("[i] Chargement de test30.csv ...")
    df_test = pd.read_csv(TEST_PATH, low_memory=False)
    print(f"    -> {len(df_test)} lignes chargées")

    df_train = _nettoyer(df_train)
    df_test  = _nettoyer(df_test)

    print(f"\n[i] Après nettoyage :")
    print(f"    Train : {len(df_train)} lignes")
    print(f"    Test  : {len(df_test)} lignes")
    print(f"\n[i] Distribution train :")
    print(df_train[LABEL_COL].value_counts().to_string())

    return df_train, df_test, FEATURES


def dispatcher_if(df_train: pd.DataFrame, df_test: pd.DataFrame, features: list):
    """
    Isolation Forest — non supervisé.
    Train : seulement le trafic légitime.
    Test  : légitime + toutes les attaques.
    """
    print("\n" + "="*50)
    print("DISPATCHING — Isolation Forest")
    print("="*50)

    X_train_if = df_train[df_train[LABEL_COL] == "legitimate"][features].values
    X_test_if  = df_test[features].values
    y_test_if  = np.where(df_test[LABEL_COL] == "legitimate", 1, -1)

    print(f"  Train IF (legitimate uniquement) : {len(X_train_if)}")
    print(f"  Test  IF                         : {len(X_test_if)}")
    print(f"    -> Normaux   : {(y_test_if ==  1).sum()}")
    print(f"    -> Anomalies : {(y_test_if == -1).sum()}")

    return X_train_if, X_test_if, y_test_if


def dispatcher_rf(df_train: pd.DataFrame, df_test: pd.DataFrame, features: list):
    """
    Random Forest — supervisé.
    Train et test avec toutes les classes encodées.
    """
    print("\n" + "="*50)
    print("DISPATCHING — Random Forest")
    print("="*50)

    le = LabelEncoder()
    le.fit(CLASSES)

    X_train_rf = df_train[features].values
    y_train_rf = le.transform(df_train[LABEL_COL].values)

    X_test_rf  = df_test[features].values
    y_test_rf  = le.transform(df_test[LABEL_COL].values)

    print(f"  Train RF : {len(X_train_rf)} échantillons")
    print(f"  Test  RF : {len(X_test_rf)} échantillons")
    print(f"  Classes  : {list(le.classes_)}")

    return X_train_rf, X_test_rf, y_train_rf, y_test_rf, le


if __name__ == "__main__":
    df_train, df_test, features = charger_dataset()
    dispatcher_if(df_train, df_test, features)
    dispatcher_rf(df_train, df_test, features)
    print("\n[✓] Dispatching terminé.")
