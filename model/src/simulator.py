"""
simulator.py
------------
Simulateur MQTT IoT — Simule tous les types d'attaques MQTTset :
  - normal      : trafic légitime d'un capteur de battements de cœur
  - flood       : envoi massif de messages
  - bruteforce  : tentatives répétées de connexion
  - malformed   : messages avec structure MQTT incorrecte
  - slowite     : attaque lente (SlowITe)
  - all         : tous les scénarios à la suite
"""

import time
import os
import random
import argparse
import paho.mqtt.publish as publish

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC       = "iot/data"


# ── Couleurs terminal ─────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"


def _send(payload: str, silent: bool = False):
    """Envoie un message MQTT et l'affiche si non silencieux."""
    try:
        publish.single(TOPIC, payload, hostname=BROKER_HOST, port=BROKER_PORT)
        if not silent:
            print(f"  → {payload[:80]}")
    except Exception as e:
        print(f"  [!] Erreur envoi : {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Trafic Normal — capteur de battements de cœur
# ─────────────────────────────────────────────────────────────────────────────
def simulate_normal(count: int = 30, interval: float = 1.0):
    print(f"\n{GREEN}[NORMAL] Trafic légitime — {count} messages (intervalle={interval}s){RESET}")
    for i in range(count):
        bpm      = 60 + random.randint(-5, 5)
        temp     = round(36.5 + random.uniform(-0.3, 0.3), 1)
        payload  = f"sensor=heart|bpm={bpm}|temp={temp}|ts={int(time.time())}"
        _send(payload)
        time.sleep(interval)
    print(f"{GREEN}[✓] Trafic normal terminé.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Attaque FLOOD — envoi massif et rapide
# ─────────────────────────────────────────────────────────────────────────────
def simulate_flood(count: int = 500):
    print(f"\n{RED}[FLOOD] Envoi de {count} messages en rafale...{RESET}")
    for i in range(count):
        _send(f"FLOOD_{i}_" + "X" * random.randint(10, 100), silent=(i % 50 != 0))
    print(f"{RED}[✓] Attaque flood terminée. ({count} messages){RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Attaque BRUTEFORCE — tentatives répétées
# ─────────────────────────────────────────────────────────────────────────────
def simulate_bruteforce(count: int = 100, interval: float = 0.05):
    print(f"\n{RED}[BRUTEFORCE] {count} tentatives de connexion...{RESET}")
    users = ["admin", "root", "user", "mqtt", "iot", "test"]
    passwds = ["123456", "password", "admin", "root", "letmein", "000000"]
    for i in range(count):
        user   = random.choice(users)
        passwd = random.choice(passwds)
        payload = f"AUTH|user={user}|pass={passwd}|attempt={i+1}"
        _send(payload, silent=(i % 20 != 0))
        time.sleep(interval)
    print(f"{RED}[✓] Bruteforce terminé.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Attaque MALFORMED — messages MQTT incorrects
# ─────────────────────────────────────────────────────────────────────────────
def simulate_malformed(count: int = 50):
    print(f"\n{YELLOW}[MALFORMED] {count} messages malformés...{RESET}")

    malformed_payloads = [
        b"\x00\xFF\xFE\xFD",                          # bytes invalides
        b"\x10\x00" * 10,                             # header MQTT cassé
        "A" * 10000,                                  # payload trop long
        "\x00\x01\x02\x03\x04\x05",                  # données binaires brutes
        '{"msg": null, "type": "\x00\xFF"}',          # JSON avec null bytes
        "mqtt://;DROP TABLE sessions;--",             # injection
        "\r\n\r\n" * 20,                              # retours chariot massifs
    ]
    for i in range(count):
        p = malformed_payloads[i % len(malformed_payloads)]
        if isinstance(p, bytes):
            try:
                publish.single(TOPIC, p, hostname=BROKER_HOST, port=BROKER_PORT)
                if i % 10 == 0:
                    print(f"  → [bytes] {p[:30]}")
            except Exception:
                pass
        else:
            _send(p, silent=(i % 10 != 0))
    print(f"{YELLOW}[✓] Messages malformés envoyés.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Attaque SLOWITE — connexions lentes (SlowITe)
# ─────────────────────────────────────────────────────────────────────────────
def simulate_slowite(count: int = 30, interval: float = 3.0):
    print(f"\n{YELLOW}[SLOWITE] {count} messages lents (intervalle={interval}s)...{RESET}")
    for i in range(count):
        # Messages très petits, très espacés — épuise les connexions
        payload = f"s={i}"
        _send(payload)
        time.sleep(interval)
    print(f"{YELLOW}[✓] Attaque SlowITe terminée.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Scénario COMPLET
# ─────────────────────────────────────────────────────────────────────────────
def simulate_all():
    print(f"\n{CYAN}{'='*55}")
    print("  SCÉNARIO COMPLET — Tous types d'attaques")
    print(f"{'='*55}{RESET}")

    simulate_normal(count=10, interval=0.5)
    time.sleep(1)

    print(f"\n{RED}--- Passage en mode FLOOD ---{RESET}")
    simulate_flood(count=200)
    time.sleep(2)

    print(f"\n{GREEN}--- Retour normal ---{RESET}")
    simulate_normal(count=5, interval=1.0)
    time.sleep(1)

    print(f"\n{RED}--- Passage en mode BRUTEFORCE ---{RESET}")
    simulate_bruteforce(count=50, interval=0.1)
    time.sleep(2)

    print(f"\n{YELLOW}--- Passage en mode MALFORMED ---{RESET}")
    simulate_malformed(count=20)
    time.sleep(2)

    print(f"\n{GREEN}--- Fin du scénario complet ---{RESET}")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulateur MQTT IDS — Architecture Hybride IF + RF",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--mode",
        choices=["normal", "flood", "bruteforce", "malformed", "slowite", "all"],
        default="normal",
        help=(
            "Mode de simulation :\n"
            "  normal     — trafic légitime d'un capteur IoT\n"
            "  flood      — envoi massif de messages\n"
            "  bruteforce — tentatives de connexion répétées\n"
            "  malformed  — messages MQTT incorrects\n"
            "  slowite    — attaque lente SlowITe\n"
            "  all        — tous les scénarios à la suite"
        )
    )
    parser.add_argument("--count",    type=int,   default=50,  help="Nombre de messages")
    parser.add_argument("--interval", type=float, default=1.0, help="Intervalle (secondes)")
    args = parser.parse_args()

    modes = {
        "normal":     lambda: simulate_normal(args.count, args.interval),
        "flood":      lambda: simulate_flood(args.count),
        "bruteforce": lambda: simulate_bruteforce(args.count, args.interval),
        "malformed":  lambda: simulate_malformed(args.count),
        "slowite":    lambda: simulate_slowite(args.count, args.interval),
        "all":        simulate_all,
    }

    modes[args.mode]()
