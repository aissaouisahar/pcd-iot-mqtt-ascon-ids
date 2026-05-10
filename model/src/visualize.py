import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report
import joblib

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR    = os.path.join(BASE_DIR, "models")
OUTPUT_DIR    = os.path.join(BASE_DIR, "logs", "graphs")
DATA_PATH     = os.path.join(BASE_DIR, "data", "test_cleaned.csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Chemins des modèles (Mise à jour selon train_hybrid.py)
IF_MODEL_PATH  = os.path.join(MODELS_DIR, "if_model.pkl")
RF_MODEL_PATH  = os.path.join(MODELS_DIR, "rf_model.pkl")
SCALER_PATH    = os.path.join(MODELS_DIR, "scaler.pkl")

FEATURES = ["tcp.time_delta", "tcp.len", "mqtt.len", "mqtt.msgtype", 
            "msg_per_sec", "entropy", "payload_ratio", "interval_std", "burst_ratio"]
TARGET = "target"

# Palette de couleurs pro
COLORS = {"Normal": "#2ecc71", "Anomalie": "#e74c3c"}

def load_data_and_models():
    print("[i] Chargement des modèles et des données de test...")
    df = pd.read_csv(DATA_PATH, low_memory=False).dropna(subset=FEATURES + [TARGET])
    
    # Échantillonnage pour la lisibilité des graphes (10 000 points suffisent)
    df_plot = df.sample(n=min(10000, len(df)), random_state=42)
    
    if_model = joblib.load(IF_MODEL_PATH)
    rf_model = joblib.load(RF_MODEL_PATH)
    scaler   = joblib.load(SCALER_PATH)
    
    return df, df_plot, if_model, rf_model, scaler

# ═══════════════════════════════════════════════════════════════════════════
# 1. DISTRIBUTION DES FEATURES (LOG SCALE)
# ═══════════════════════════════════════════════════════════════════════════
def plot_distributions(df_plot):
    print("[1] Génération des distributions...")
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    fig.suptitle("Analyse des Caractéristiques : Trafic Normal vs Attaques", fontsize=16)
    
    for i, col in enumerate(FEATURES):
        ax = axes[i//3, i%3]
        sns.kdeplot(data=df_plot, x=col, hue=TARGET, ax=ax, fill=True, common_norm=False)
        ax.set_title(f"Distribution de {col}")
        # On utilise une échelle log si les valeurs sont très dispersées (ex: msg_per_sec)
        if df_plot[col].max() > 100:
            ax.set_xscale('log')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(os.path.join(OUTPUT_DIR, "1_distributions.png"))
    plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# 2. MATRICE DE CONFUSION HYBRIDE (RÉEL VS PRÉDIT)
# ═══════════════════════════════════════════════════════════════════════════
def plot_confusion_hybrid(df_test, if_model, rf_model, scaler):
    print("[2] Génération de la matrice de confusion hybride...")
    X = df_test[FEATURES].values
    y_true = (df_test[TARGET] != "legitimate").astype(int)
    
    # Simulation du pipeline hybride
    X_scaled = scaler.transform(X)
    is_anomaly_if = (if_model.predict(X_scaled) == -1)
    
    # Décision finale (Seuil 95% comme dans l'IPS)
    pred_final = np.zeros(len(df_test))
    if is_anomaly_if.sum() > 0:
        probs_rf = rf_model.predict_proba(X[is_anomaly_if])
        classes_rf = rf_model.classes_.tolist()
        idx_legit = classes_rf.index("legitimate")
        
        # On ne garde que les attaques avec certitude > 95%
        pred_final[is_anomaly_if] = (probs_rf[:, idx_legit] < 0.05).astype(int)

    cm = confusion_matrix(y_true, pred_final)
    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Normal", "Attaque"])
    disp.plot(cmap="Blues", ax=ax)
    ax.set_title("Matrice de Confusion : Architecture Hybride (Test)")
    
    plt.savefig(os.path.join(OUTPUT_DIR, "2_confusion_hybride.png"))
    plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# 3. IMPORTANCE DES FEATURES (LE "CERVEAU" DU RANDOM FOREST)
# ═══════════════════════════════════════════════════════════════════════════
def plot_importance(rf_model):
    print("[3] Génération de l'importance des features...")
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)

    plt.figure(figsize=(10, 6))
    plt.title("Importance des caractéristiques (Random Forest)")
    plt.barh(range(len(indices)), importances[indices], color='#3498db', align='center')
    plt.yticks(range(len(indices)), [FEATURES[i] for i in indices])
    plt.xlabel('Importance Relative (Gini)')
    
    plt.savefig(os.path.join(OUTPUT_DIR, "3_feature_importance.png"))
    plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# 4. SCATTER PLOT 2D : ENTROPIE VS FRÉQUENCE
# ═══════════════════════════════════════════════════════════════════════════
def plot_scatter_security(df_plot):
    print("[4] Génération du nuage de points...")
    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=df_plot, x="msg_per_sec", y="entropy", hue=TARGET, alpha=0.6)
    plt.xscale('log')
    plt.title("Visualisation des Menaces : Fréquence vs Entropie")
    plt.xlabel("Messages par seconde (Log Scale)")
    plt.ylabel("Entropie de Shannon")
    
    plt.savefig(os.path.join(OUTPUT_DIR, "4_scatter_threats.png"))
    plt.close()

if __name__ == "__main__":
    df_test, df_plot, if_model, rf_model, scaler = load_data_and_models()
    
    plot_distributions(df_plot)
    plot_confusion_hybrid(df_test, if_model, rf_model, scaler)
    plot_importance(rf_model)
    plot_scatter_security(df_plot)
    
    print(f"\n[✓] Visualisation terminée. Graphes disponibles dans : {OUTPUT_DIR}")