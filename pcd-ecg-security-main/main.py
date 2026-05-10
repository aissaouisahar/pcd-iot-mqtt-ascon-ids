import ascon
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn
import json  # ← NOUVEAU
 
# ── CONFIGURATION ──────────────────────────────────────────────────────────────
app = FastAPI(title="Backend ECG Sécurisé ENSI 2026")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
API_KEY    = "ma_cle_secrete_ensi_2026"
 

ASCON_KEY = bytes([
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F
])
 
DATABASE   = 'ecg.db'
MQTT_TOPIC = "iot/sensor/ecg"

ASCON_AD = b'ENSI_IOT'  # Identique à l'ESP32
 
# ── BASE DE DONNÉES ───────────
def get_conn():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
 
def init_db():
    conn = get_conn()
    cur  = conn.cursor()
 
    # Médecins
    cur.execute('''CREATE TABLE IF NOT EXISTS medecins (
        idMedecin INTEGER PRIMARY KEY AUTOINCREMENT,
        nom       TEXT NOT NULL,
        prenom    TEXT NOT NULL,
        email     TEXT UNIQUE NOT NULL,
        password  TEXT NOT NULL
    )''')
 
    # Patients
    cur.execute('''CREATE TABLE IF NOT EXISTS patients (
        idPatient     INTEGER PRIMARY KEY AUTOINCREMENT,
        nom           TEXT NOT NULL,
        prenom        TEXT NOT NULL,
        age           INTEGER NOT NULL,
        telephone     TEXT,
        email         TEXT,
        dateNaissance TEXT,
        medecin_id    INTEGER NOT NULL,
        device_id     TEXT,
        FOREIGN KEY(medecin_id) REFERENCES medecins(idMedecin)
    )''')
 
    # ECGData
    cur.execute('''CREATE TABLE IF NOT EXISTS ecg_data (
        idECG      INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        taille     REAL,
        date       DATETIME DEFAULT CURRENT_TIMESTAMP,
        valeur     REAL NOT NULL,
        bpm        INTEGER,
        FOREIGN KEY(patient_id) REFERENCES patients(idPatient)
    )''')
 
    # Médecin de test
    cur.execute('''INSERT OR IGNORE INTO medecins (idMedecin, nom, prenom, email, password)
        VALUES (1, 'Bensalem', 'Ahmed', 'ahmed@ensi.tn', 'password123')''')
 
    # Patients de test
    cur.execute('''INSERT OR IGNORE INTO patients
        (idPatient, nom, prenom, age, telephone, email, dateNaissance, medecin_id, device_id)
        VALUES (1, 'Soussi', 'Abdallah', 33, '+216 55 123 456', 'abdallah@mail.com', '1991-04-15', 1, 'ESP32_ECG_Sensor')''')
    
    cur.execute('''INSERT OR IGNORE INTO patients
        (idPatient, nom, prenom, age, telephone, email, dateNaissance, medecin_id)
        VALUES (2, 'Mansouri', 'Fatma', 27, '+216 22 987 654', 'fatma@mail.com', '1997-09-03', 1)''')
 
    conn.commit()
    conn.close()
    print(" Base de données initialisée.")
 
init_db()
 
# ── MQTT ───────────────────────────────────────────────────────────────────────
latest_data = {}
 
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"MQTT connecté. Abonné à : {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f" Échec connexion MQTT, code={rc}")
 
def on_message(client, userdata, msg):
    """
    CALLBACK MQTT ADAPTÉ POUR ESP32 + IDS
    
    Format attendu :
      Base64( Nonce[16] + Ciphertext[N] + Tag[16] )
    
    Contenu déchiffré (JSON) :
      {"id": 50, "ecg": 2055, "bpm": 78, "ip": "...", "rssi": -60}
    """
    try:
        payload = msg.payload
        print(f" Message reçu — topic: {msg.topic}  taille: {len(payload)} octets")
 
        # Décoder Base64
        import base64
        full_packet = base64.b64decode(payload)
 
        if len(full_packet) < 32:  # Minimum : 16 (nonce) + 16 (tag)
            print(" Paquet trop court, ignoré.")
            return
 
        # Extraire nonce et ciphertext
        nonce      = full_packet[:16]
        ciphertext_with_tag = full_packet[16:]
 
        # Déchiffrement ASCON

        decrypted  = ascon.ascon_decrypt(
            ASCON_KEY, 
            nonce, 
            ASCON_AD,  # ← Associated Data
            ciphertext_with_tag, 
            variant="Ascon-AEAD128"
        )
        if decrypted is None:
            print(" Déchiffrement échoué (tag mismatch)")
            return
 
        # Parser le JSON
        data = json.loads(decrypted.decode('utf-8'))
        
        # Extraire les valeurs
        ecg_value = data.get('ecg')
        bpm_value = data.get('bpm')
        msg_id    = data.get('id')
        
        print(f"Déchiffré : ID={msg_id}, ECG={ecg_value}, BPM={bpm_value}")
 
    
        
        conn = get_conn()
        cur  = conn.cursor()
      
        cur.execute(
            "SELECT idPatient FROM patients WHERE device_id = ? OR idPatient = 1",
            ("ESP32_ECG_Sensor",)  # Fallback sur patient 1
        )
        patient = cur.fetchone()
        
        if patient:
            patient_id = patient['idPatient']
            
            # Mise à jour latest_data
            latest_data[patient_id] = {
                "ecg": ecg_value,
                "bpm": bpm_value,
                "id": msg_id
            }
            
            # Sauvegarde en base de données
            cur.execute(
                "INSERT INTO ecg_data (patient_id, valeur, bpm) VALUES (?, ?, ?)",
                (patient_id, ecg_value, bpm_value)
            )
            conn.commit()
            print(f" ECG sauvegardé pour patient_id={patient_id}")
        else:
            print(f"  Aucun patient associé à cet ESP32")
        
        conn.close()
 
    except json.JSONDecodeError as e:
        print(f" Erreur JSON : {e}")
    except Exception as e:
        print(f" Erreur : {e}")
        import traceback
        traceback.print_exc()
 
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

BROKER_IP = "10.43.209.150"  
 
try:
    mqtt_client.connect(BROKER_IP, 1883, 60)
    mqtt_client.loop_start()
    print(f" Tentative connexion MQTT : {BROKER_IP}:1883")
except Exception as e:
    print(f" Broker MQTT inaccessible : {e}")
 

def check_token(token: str):
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Token invalide")
 
@app.post("/login")
async def login(credentials: dict):
    conn = get_conn()
    user = conn.execute(
        "SELECT idMedecin, nom, prenom, email FROM medecins WHERE email = ? AND password = ?",
        (credentials.get("email"), credentials.get("password"))
    ).fetchone()
    conn.close()
    if user:
        return {
            "status": "success",
            "token": API_KEY,
            "medecin": {
                "id": user["idMedecin"],
                "nom": user["nom"],
                "prenom": user["prenom"],
                "email": user["email"],
            }
        }
    raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
 
@app.get("/patients")
async def get_patients(token: str):
    check_token(token)
    conn = get_conn()
    rows = conn.execute(
        "SELECT idPatient, nom, prenom, age, telephone, email, dateNaissance, device_id FROM patients"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
 
@app.get("/medecin/{mid}/patients")
async def get_patients_by_medecin(mid: int, token: str):
    check_token(token)
    conn = get_conn()
    rows = conn.execute(
        "SELECT idPatient, nom, prenom, age, telephone, email, dateNaissance, device_id FROM patients WHERE medecin_id = ?",
        (mid,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
 
@app.post("/patients/add")
async def add_patient(p: dict, token: str):
    check_token(token)
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO patients (nom, prenom, age, telephone, email, dateNaissance, medecin_id, device_id) VALUES (?,?,?,?,?,?,?,?)",
            (p['nom'], p['prenom'], p['age'], p.get('telephone',''), p.get('email',''), p.get('dateNaissance',''), p.get('medecin_id', 1), p.get('device_id',''))
        )
        conn.commit()
        conn.close()
        return {"message": "Patient créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
 
@app.get("/patients/{p_id}/ecg")
async def get_ecg_history(p_id: int, token: str):
    check_token(token)
    conn = get_conn()
    rows = conn.execute(
        "SELECT idECG, date, valeur, bpm, taille FROM ecg_data WHERE patient_id = ? ORDER BY idECG DESC LIMIT 100",
        (p_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
 
@app.get("/live/{p_id}")
async def get_live(p_id: int, token: str):
    """
    Retourne les dernières données ECG temps réel pour un patient.
    
    Adapté pour ESP32 : retourne {ecg, bpm, id}
    """
    check_token(token)
    data = latest_data.get(p_id, {})
    return {
        "patient_id": p_id, 
        "ecg": data.get("ecg"),
        "bpm": data.get("bpm"),
        "msg_id": data.get("id")
    }
 
if __name__ == "__main__":
    print("=" * 70)
    print("  Backend FastAPI — Application ECG ENSI 2026")
    print("  Adapté pour ESP32 + IDS + ASCON")
    print("=" * 70)
    print(f"[CONFIG] MQTT Broker : {BROKER_IP}:1883")
    print(f"[CONFIG] MQTT Topic  : {MQTT_TOPIC}")
    print(f"[CONFIG] ASCON Key   : {ASCON_KEY.hex()}")
    print(f"[CONFIG] API         : http://127.0.0.1:8000")
    print("=" * 70)
    uvicorn.run(app, host="127.0.0.1", port=8000)

