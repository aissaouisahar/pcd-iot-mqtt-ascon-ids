#!/usr/bin/env python3
"""
Moniteur ECG en temps réel
Lit les données du capteur AD8232 via le port série de l'ESP32
Affiche et trace la courbe ECG en direct
"""

import serial
import sys
import time
import re
from collections import deque
import threading

# Configuration
SERIAL_PORT = "/dev/ttyACM0"  
BAUD_RATE = 115200
MAX_POINTS = 200  

# Données
ecg_values = deque(maxlen=MAX_POINTS)
bpm_values = deque(maxlen=20)
timestamps = deque(maxlen=MAX_POINTS)
start_time = time.time()
data_lock = threading.Lock()

def parse_ecg_line(line: str) -> dict | None:
    """
    Parse une ligne du port série
    Format: "Min:1000,Max:3000,ECG:2456.78,BPM:78"
    """
    try:
        match_ecg = re.search(r'ECG:(\d+\.?\d*)', line)
        match_bpm = re.search(r'BPM:(\d+)', line)
        
        if match_ecg:
            return {
                'ecg': float(match_ecg.group(1)),
                'bpm': int(match_bpm.group(1)) if match_bpm else 0
            }
    except Exception as e:
        pass
    
    return None

def read_serial():
    """Thread pour lire le port série"""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"[SERIAL] ✓ Connecté à {SERIAL_PORT} @ {BAUD_RATE} baud\n")
        
        while True:
            try:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                    
                        data = parse_ecg_line(line)
                        if data:
                            with data_lock:
                                elapsed = time.time() - start_time
                                ecg_values.append(data['ecg'])
                                timestamps.append(elapsed)
                                if data['bpm'] > 0:
                                    bpm_values.append(data['bpm'])
                        else:
                            # Afficher les autres messages de debug
                            if not line.startswith("[DEBUG]"):
                                print(f"[ESP32] {line}")
                
                time.sleep(0.001)
                
            except UnicodeDecodeError:
                continue
    
    except serial.SerialException as e:
        print(f"[SERIAL] ✗ Erreur: {e}")
        print(f"[HINT] Essayez: dmesg | grep ttyUSB ou ls /dev/ttyUSB*")
        sys.exit(1)

def display_graph_terminal():
    """Affiche un graphique ASCII du signal ECG"""
    min_val = 1000
    max_val = 3000
    height = 10
    width = 50
    
    print("\n" + "=" * 70)
    print(" COURBE ECG EN TEMPS RÉEL (ASCII)")
    print("=" * 70)
    
    while True:
        with data_lock:
            if len(ecg_values) > 5:
                
                vals = list(ecg_values)
                range_val = max_val - min_val
                
                
                graph = []
                for val in vals[-width:]:
                    
                    normalized = (val - min_val) / range_val * height
                    normalized = max(0, min(height - 1, int(normalized)))
                    graph.append(normalized)
                
                # Afficher
                print("\r", end="")
                for row in range(height - 1, -1, -1):
                    line = ""
                    for col, g in enumerate(graph):
                        if g >= row:
                            line += "ok"
                        else:
                            line += " "
                    print(f"{1000 + (row + 1) * (2000 // height):4d}mV │{line}│", end="")
                    if row > 0:
                        print("\n", end="")
                
                print()
                print("     └" + "─" * width + "┘")
                
                # Stats
                avg_ecg = sum(ecg_values) / len(ecg_values)
                avg_bpm = sum(bpm_values) / len(bpm_values) if bpm_values else 0
                
                print(f"\n Stats: ECG={avg_ecg:.0f}mV | HR={avg_bpm:.0f}bpm | N={len(ecg_values)} pts", end="")
                print(" " * 20)
        
        time.sleep(0.5)

def display_numeric():
    """Affiche les valeurs numériques"""
    while True:
        with data_lock:
            if ecg_values:
                avg_ecg = sum(ecg_values) / len(ecg_values)
                min_ecg = min(ecg_values)
                max_ecg = max(ecg_values)
                avg_bpm = sum(bpm_values) / len(bpm_values) if bpm_values else 0
                
                print(f"\r[ECG] Avg={avg_ecg:7.1f}mV | Min={min_ecg:7.1f} | Max={max_ecg:7.1f} | HR={avg_bpm:6.1f}bpm | Pts={len(ecg_values):3d}", end="", flush=True)
        
        time.sleep(0.2)

if __name__ == "__main__":
    print("=" * 70)
    print(" ECG MONITOR - Capteur AD8232 via ESP32")
    print("=" * 70)
    print(f"Port série: {SERIAL_PORT}")
    print(f"Baud rate: {BAUD_RATE}")
    print("\nEn attente de données...\n")
    
    # Lancer le thread de lecture série
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()
    
    # Lancer l'affichage
    try:
        display_numeric()
    except KeyboardInterrupt:
        print("\n\n✋ Arrêt...")
        sys.exit(0)
