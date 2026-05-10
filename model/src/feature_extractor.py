import time
import math
from collections import deque

class FeatureExtractor:
    """
    Extracteur de caractéristiques temps-réel pour IDS/IPS MQTT.
    Compatible avec des flux de données CHIFFRÉES.
    Génère 9 features synchronisées avec le preprocessing.
    """

    def __init__(self, window_sec: float = 5.0):
        """
        Args:
            window_sec: Taille de la fenêtre glissante pour les calculs de fréquence (secondes).
        """
        self.window_sec = window_sec
        self.timestamps = deque()   # Historique des arrivées pour msg_per_sec
        self.intervals  = deque(maxlen=20) # Historique des délais pour interval_std
        self.last_time  = time.time()

    def _calculate_entropy(self, data: bytes) -> float:
        """
        Calcule l'entropie de Shannon sur les octets bruts.
        Utile pour détecter des anomalies dans les paquets chiffrés.
        """
        if not data:
            return 0.0
        
        # Compter la fréquence de chaque octet (0-255)
        freq = {}
        for b in data:
            freq[b] = freq.get(b, 0) + 1
        
        n = len(data)
        entropy = -sum((c/n) * math.log2(c/n) for c in freq.values())
        return entropy

    def _purge_old_data(self, now: float):
        """Supprime les données hors de la fenêtre temporelle."""
        cutoff = now - self.window_sec
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

    def extract(self, payload_bytes: bytes) -> list:
        """
        Extrait les 9 caractéristiques d'un message MQTT.
        Prend des 'bytes' en entrée (compatible données chiffrées).
        """
        now = time.time()
        
        # 1. tcp.time_delta : Temps écoulé depuis le message précédent
        time_delta = now - self.last_time
        self.last_time = now

        # Mise à jour des fenêtres statistiques
        self.timestamps.append(now)
        self._purge_old_data(now)
        self.intervals.append(time_delta)

        # 2. tcp.len : Estimation de la taille totale du paquet TCP
        # Formule synchronisée avec le preprocessing (Headers IP/TCP estimés à 52 octets)
        mqtt_len = len(payload_bytes)
        tcp_len  = mqtt_len + 52 

        # 3. mqtt.len : Taille réelle de la charge utile (chiffrée)
        # Déjà calculé ci-dessus

        # 4. mqtt.msgtype : Type de message MQTT 
        # Fixé à 3 (PUBLISH) car l'IPS analyse les données des capteurs
        msg_type = 3 

        # 5. msg_per_sec : Fréquence d'envoi (Messages par seconde)
        msg_per_sec = len(self.timestamps) / self.window_sec

        # 6. entropy : Complexité des données (Shannon Entropy)
        entropy = self._calculate_entropy(payload_bytes)

        # 7. payload_ratio : Ratio de données utiles par rapport au paquet total
        payload_ratio = mqtt_len / (tcp_len + 1e-6)

        # 8. interval_std : Écart-type des intervalles (Stabilité du flux)
        if len(self.intervals) > 1:
            mean = sum(self.intervals) / len(self.intervals)
            interval_std = math.sqrt(sum((x - mean)**2 for x in self.intervals) / len(self.intervals))
        else:
            interval_std = 0.0

        # 9. burst_ratio : Détection de rafales (Messages arrivés en < 100ms)
        burst_count = sum(1 for i in self.intervals if i < 0.1)
        burst_ratio = burst_count / len(self.intervals) if self.intervals else 0.0

        # RETOURNE L'ORDRE EXACT REQUIS PAR LE MODÈLE
        return [
            float(time_delta),    # 1
            float(tcp_len),       # 2
            float(mqtt_len),      # 3
            float(msg_type),      # 4
            float(msg_per_sec),   # 5
            float(entropy),       # 6
            float(payload_ratio), # 7
            float(interval_std),  # 8
            float(burst_ratio)    # 9
        ]