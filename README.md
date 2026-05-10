# Sécurisation IoT MQTT par ASCON et IDS basé IA


##  Description

Système IoT sécurisé pour la **surveillance ECG à distance** avec :
- Capteur ECG **AD8232** connecté à un **ESP32**
- Chiffrement léger **ASCON-AEAD128** (Standard NIST 2025)
- **Model AI** (Random Forest + Isolation Forest) intermédiaire
- Application web full-stack (Backend Python + Frontend React)
- Simulateur d'attaques 

##  Architecture

\`\`\`
ESP32 + AD8232 (Publisher)
         ↓ ASCON-AEAD128
   topic: iot/sensor/ecg/raw
         ↓
   Filtre IA (analyse + filtre)
         ↓ si données saines
   topic: iot/sensor/ecg
         ↓
   Application full-stack
   ├─ Backend Python (Flask)
   ├─ Base SQLite
   └─ Frontend React
\`\`\`

## Innovation : Le modèle IA pour detection des attaques 

Le modèle IA fait office de **filtre** entre le capteur et l'application : il analyse chaque message ECG, détecte les attaques (DoS, MitM, Bruteforce, anomalies) et ne laisse passer que les données saines vers l'application finale.

##  Structure du projet

\`\`\`
proj1/
├── src/                          
│   ├── main.cpp                  
│   ├── ascon.h / ascon.cpp      
│   ├── test.h                    
│   ├── ascon.py                  
│   ├── subscriber.py             
│   └── ecg_monitor.py            
│
├── model/                        
│   ├── data/                     
│   ├── models/                   
│   ├── src/                      
│   └── logs/                     
├── pcd-ecg-security-main/        
│   ├── main.py                   
│   ├── ecg.db                    
│   ├── ascon.py                  
│   ├── frontend-ecg/             
│   └── requirements.txt
│
├── attack_simulator.py           
├── platformio.ini                
└── README.md
\`\`\`



### Prérequis
- Ubuntu 22.04+
- Python 3.12+
- Node.js 18+
- VS Code + extension PlatformIO
- ESP32 + AD8232 + électrodes


## Licence

Ce projet est sous licence MIT - voir [LICENSE](LICENSE) pour plus de détails.
