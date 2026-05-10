#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "ascon.h"
 

// CONFIGURATION WIFI & MQTT

 
const char* ssid        = "Redmi";
const char* password    = "sahar1234nnn";
const char* mqtt_server = "10.43.209.150";
 
const char* topic_pub    = "iot/sensor/ecg/raw";
const char* topic_status = "iot/esp32/status";
 


#define DEMO_MODE true              
#define DEMO_DETAIL_EVERY_N 5       


 
const int MQTT_PUB_INTERVAL = 500;  
unsigned long lastMqttPub = 0;
 

// ASCON CRYPTO

 
const uint8_t ASCON_KEY[ASCON_KEY_LEN] = {
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F
};
 
const uint8_t AD[8]  = {'E', 'N', 'S', 'I', '_', 'I', 'O', 'T'};
const size_t  ADLEN = 8;


const int ECG_BASELINE  = 2048;
const int ECG_AMPLITUDE = 600;
const int BPM_MIN       = 55;      
const int BPM_MAX       = 105;
 
struct ECGSimulator {
    int current_bpm;
    unsigned long time_ms;
    unsigned long last_bpm_change;
    
    
    int baseline_drift;          
    bool electrode_loose;        
    int electrode_loose_counter; 
    int muscle_artifact_level;   
    int extrasystole_counter;    
};

ECGSimulator ecg_state = {75, 0, 0, 0, false, 0, 5, 0};



float gaussianApprox(float x, float center, float width) {
    float delta = x - center;
    float t = (delta * delta) / (2.0 * width * width);
    if (t > 5.0) return 0.0;
    return 1.0 / (1.0 + t + t*t*0.5);
}

int powerLineNoise(unsigned long time_ms) {
    float phase_50hz = (time_ms % 20) / 20.0 * 2.0 * 3.14159;
    return (int)(15 * sin(phase_50hz));  
}

int baselineDrift(unsigned long time_ms) {
    
    float resp_phase = (time_ms % 4000) / 4000.0 * 2.0 * 3.14159;
    int respiration = (int)(40 * sin(resp_phase));
    
    
    float drift_phase = (time_ms % 60000) / 60000.0 * 2.0 * 3.14159;
    int slow_drift = (int)(60 * sin(drift_phase));
    
    return respiration + slow_drift;
}

// Bruit musculaire (EMG) - quand le patient bouge
int muscleArtifact() {
    if (ecg_state.muscle_artifact_level > 0) {
        // Bruit haute fréquence aléatoire
        int noise = random(-ecg_state.muscle_artifact_level * 30, 
                          ecg_state.muscle_artifact_level * 30);
        ecg_state.muscle_artifact_level--;
        return noise;
    }
    return 0;
}


int electrodeLooseEffect() {
    if (ecg_state.electrode_loose) {
        ecg_state.electrode_loose_counter--;
        if (ecg_state.electrode_loose_counter <= 0) {
            ecg_state.electrode_loose = false;
            Serial.println("[AD8232] Électrode reconnectée");
        }
        
        return random(0, 2) ? 1500 : -1500;
    }
    return 0;
}

int simulateECGValue(float t_in_beat, float beat_duration) {
    float phase = (beat_duration > 0) ? (t_in_beat / beat_duration) : 0;
    
    // Composantes ECG normales
    float p_wave = 80 * gaussianApprox(phase, 0.15, 0.04);   
    float qrs = ECG_AMPLITUDE * gaussianApprox(phase, 0.30, 0.04);
    float q_wave = -100 * gaussianApprox(phase, 0.27, 0.02);  
    float s_wave = -150 * gaussianApprox(phase, 0.33, 0.02);  
    float t_wave = (ECG_AMPLITUDE / 3.0) * gaussianApprox(phase, 0.60, 0.08);
    float u_wave = 30 * gaussianApprox(phase, 0.75, 0.05);    
    
    // Bruits réalistes AD8232
    int noise_random = random(-12, 13);                    
    int noise_50hz   = powerLineNoise(ecg_state.time_ms);  
    int drift        = baselineDrift(ecg_state.time_ms);   
    int muscle       = muscleArtifact();                   
    int electrode    = electrodeLooseEffect();             
    
    // Somme totale
    int ecg_value = ECG_BASELINE 
                  + (int)p_wave + (int)q_wave + (int)qrs + (int)s_wave 
                  + (int)t_wave + (int)u_wave
                  + noise_random + noise_50hz + drift + muscle + electrode;
    
    // Clipper
    if (ecg_value < 0) ecg_value = 0;
    if (ecg_value > 4095) ecg_value = 4095;
    
    return ecg_value;
}

void updateBPM() {
    unsigned long now = millis();
    
   
    if (now - ecg_state.last_bpm_change > 2500) {
        if (random(0, 100) < 25) {  
            
            int delta = random(-3, 4);
            
            
            if (random(0, 100) < 5) {
                delta = random(-8, 9);
            }
            
            ecg_state.current_bpm += delta;
            
            if (ecg_state.current_bpm < BPM_MIN) ecg_state.current_bpm = BPM_MIN;
            if (ecg_state.current_bpm > BPM_MAX) ecg_state.current_bpm = BPM_MAX;
            
            ecg_state.last_bpm_change = now;
        }
    }
    
    
    if (random(0, 1000) < 10) {
        ecg_state.muscle_artifact_level = random(8, 15);
        if (DEMO_MODE) Serial.println("[AD8232]  Mouvement patient détecté (EMG)");
    }
    
    
    if (random(0, 1000) < 3 && !ecg_state.electrode_loose) {
        ecg_state.electrode_loose = true;
        ecg_state.electrode_loose_counter = random(4, 9);
        if (DEMO_MODE) Serial.println("[AD8232]  ÉLECTRODE DÉCONNECTÉE !");
    }
    
    
    if (random(0, 1000) < 20) {
        ecg_state.extrasystole_counter = 1;
        if (DEMO_MODE) Serial.println("[ECG]  Extrasystole détectée");
    }
}

int getNextECGSample() {
    float beat_duration_ms = 60000.0 / ecg_state.current_bpm;
    
    
    if (ecg_state.extrasystole_counter > 0) {
        beat_duration_ms *= 0.6;
        ecg_state.extrasystole_counter--;
    }
    
    float t_in_beat = fmod(ecg_state.time_ms, beat_duration_ms);
    int ecg_value = simulateECGValue(t_in_beat, beat_duration_ms);
    
    ecg_state.time_ms += MQTT_PUB_INTERVAL;
    return ecg_value;
}




void printHex(const char* label, const uint8_t* data, size_t len, int bytes_per_line = 16) {
    Serial.printf("  %s (%d bytes):\n", label, len);
    Serial.print("    ");
    for (size_t i = 0; i < len; i++) {
        Serial.printf("%02X ", data[i]);
        if ((i + 1) % bytes_per_line == 0 && i < len - 1) {
            Serial.print("\n    ");
        }
    }
    Serial.println();
}

// BASE64


static const char b64chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

String base64Encode(const uint8_t* data, size_t len) {
    String out = "";
    int i = 0;
    uint8_t buf3[3], buf4[4];
    while (len--) {
        buf3[i++] = *data++;
        if (i == 3) {
            buf4[0] = (buf3[0] & 0xfc) >> 2;
            buf4[1] = ((buf3[0] & 0x03) << 4) + ((buf3[1] & 0xf0) >> 4);
            buf4[2] = ((buf3[1] & 0x0f) << 2) + ((buf3[2] & 0xc0) >> 6);
            buf4[3] = buf3[2] & 0x3f;
            for (int k = 0; k < 4; k++) out += b64chars[buf4[k]];
            i = 0;
        }
    }
    if (i) {
        for (int j = i; j < 3; j++) buf3[j] = 0;
        buf4[0] = (buf3[0] & 0xfc) >> 2;
        buf4[1] = ((buf3[0] & 0x03) << 4) + ((buf3[1] & 0xf0) >> 4);
        buf4[2] = ((buf3[1] & 0x0f) << 2) + ((buf3[2] & 0xc0) >> 6);
        buf4[3] = buf3[2] & 0x3f;
        for (int k = 0; k < i + 1; k++) out += b64chars[buf4[k]];
        while (i++ < 3) out += '=';
    }
    return out;
}

// CHIFFREMENT ASCON 


WiFiClient   espClient;
PubSubClient client(espClient);
int          compteur = 0;

void publishEncrypted(const char* topic, const char* plaintext) {
    size_t ptlen = strlen(plaintext);
    
    
    bool show_details = DEMO_MODE && (compteur % DEMO_DETAIL_EVERY_N == 0);

    // 1. nonce aléatoire 16 octets
    uint8_t nonce[ASCON_NONCE_LEN];
    esp_fill_random(nonce, ASCON_NONCE_LEN);

    // 2. Buffer ciphertext = ptlen + 16 (tag)
    size_t ctlen = ptlen + ASCON_TAG_LEN;
    uint8_t* ciphertext = (uint8_t*)malloc(ctlen);
    if (!ciphertext) {
        Serial.println("[ASCON] Erreur malloc");
        return;
    }

    // 3. Chiffrement ASCON-AEAD128 
    unsigned long t0 = micros();
    ascon_aead_encrypt(ASCON_KEY, nonce, AD, ADLEN,
                       (const uint8_t*)plaintext, ptlen,
                       ciphertext);
    unsigned long elapsed = micros() - t0;

    // 4. Encoder en Base64
    size_t totalLen = ASCON_NONCE_LEN + ctlen;
    uint8_t* fullPacket = (uint8_t*)malloc(totalLen);
    if (!fullPacket) {
        free(ciphertext);
        return;
    }
    memcpy(fullPacket, nonce, ASCON_NONCE_LEN);
    memcpy(fullPacket + ASCON_NONCE_LEN, ciphertext, ctlen);
    
    String b64 = base64Encode(fullPacket, totalLen);

    // 5. Publication MQTT
    client.publish(topic, b64.c_str());
    
 
    if (show_details) {
        Serial.println();
        Serial.println("┌─────────────────────────────────────────────────────────────┐");
        Serial.printf( "│  ASCON-AEAD128 — Message #%-4d                              │\n", compteur);
        Serial.println("└─────────────────────────────────────────────────────────────┘");
        
        // Plaintext (JSON lisible)
        Serial.println("\n  PLAINTEXT (JSON original) :");
        Serial.printf("    %s\n", plaintext);
        Serial.printf("    Taille: %d bytes\n", ptlen);
        
        // Clé
        Serial.println("\n   CLÉ ASCON (128 bits) :");
        Serial.print("    ");
        for (int i = 0; i < ASCON_KEY_LEN; i++) Serial.printf("%02X ", ASCON_KEY[i]);
        Serial.println();
        
        // Nonce
        printHex("NONCE (aléatoire, 128 bits)", nonce, ASCON_NONCE_LEN);
        
        // Données associées
        Serial.println("\n    ASSOCIATED DATA :");
        Serial.print("    ASCII: \"");
        for (size_t i = 0; i < ADLEN; i++) Serial.printf("%c", AD[i]);
        Serial.println("\"");
        Serial.print("    HEX:   ");
        for (size_t i = 0; i < ADLEN; i++) Serial.printf("%02X ", AD[i]);
        Serial.println();
        
        // Ciphertext (sans le tag)
        printHex("CIPHERTEXT (données chiffrées)", ciphertext, ptlen);
        
        // Tag d'authentification
        printHex(" TAG AUTHENTIFICATION (128 bits)", ciphertext + ptlen, ASCON_TAG_LEN);
        
        // Performance
        Serial.printf("\n    PERFORMANCE :\n");
        Serial.printf("    Temps de chiffrement: %lu µs (%.3f ms)\n", elapsed, elapsed/1000.0);
        Serial.printf("    Débit: %.2f KB/s\n", (ptlen / (elapsed / 1000000.0)) / 1024.0);
        
        // Paquet final Base64 (envoyé sur MQTT)
        Serial.println("\n   PAQUET MQTT FINAL (Base64) :");
        Serial.printf("    Longueur: %d bytes\n", b64.length());
        Serial.print("    ");
       
        for (int i = 0; i < b64.length(); i++) {
            Serial.print(b64[i]);
            if ((i + 1) % 60 == 0) Serial.print("\n    ");
        }
        Serial.println();
        
        Serial.println("\n   Topic: " + String(topic));
        Serial.println("   Statut:  Publié sur le broker");
        Serial.println("──────────────────────────────────────────────────────────────");
        Serial.println();
    }

    free(ciphertext);
    free(fullPacket);
}


// CALLBACK MQTT


void callback(char* topic, byte* payload, unsigned int length) {
    // Pour réception de commandes futures
}


// RECONNEXION


void reconnect() {
    while (!client.connected()) {
        Serial.print("[MQTT] Connexion au broker...");
        if (client.connect("ESP32_ECG_Sensor")) {
            Serial.println(" Connecté !");
            client.publish(topic_status, "ESP32 ECG en ligne");
        } else {
            Serial.print(" Échec (rc=");
            Serial.print(client.state());
            Serial.println(") — réessai dans 5s...");
            delay(5000);
        }
    }
}


// SETUP


void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println();
    Serial.println("╔═══════════════════════════════════════════════════════════════╗");
    Serial.println("║  ESP32 + MQTT + ASCON-AEAD128                                 ║");
    Serial.println("║  ECG réaliste AD8232 Sensor                                   ║");
    Serial.println("║  Projet PCD ENSI 2025/2026                                    ║");
    Serial.println("╚═══════════════════════════════════════════════════════════════╝");
    
    if (DEMO_MODE) {
        Serial.println("\n[DEMO] Mode démo activé");
        Serial.printf("[DEMO] Détails ASCON tous les %d messages\n", DEMO_DETAIL_EVERY_N);
    }
    
   
    randomSeed(analogRead(0));
    
 
    ecg_state.current_bpm = random(BPM_MIN, BPM_MAX + 1);
    Serial.printf("[ECG] BPM initial : %d\n", ecg_state.current_bpm);
    Serial.println("[AD8232] Simulation : bruit 50Hz, drift baseline, EMG, électrodes");

    // Connexion WiFi
    Serial.print("\n[WIFI] Connexion à: ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n[WIFI] Connecté ! IP: " + WiFi.localIP().toString());
    Serial.printf("[WIFI] RSSI: %ld dBm\n", (long)WiFi.RSSI());

    // Configuration MQTT
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
    client.setBufferSize(512);

    Serial.println("\n[SYS] Prêt à publier sur: " + String(topic_pub));
    Serial.println("═══════════════════════════════════════════════════════════════\n");
}


// LOOP


void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    unsigned long now = millis();
    
    if (now - lastMqttPub >= MQTT_PUB_INTERVAL) {
        lastMqttPub = now;
        compteur++;
        
        updateBPM();
        
        int ecgVal = getNextECGSample();
        int bpmVal = ecg_state.current_bpm;

        
        char plaintext[128];
        sprintf(plaintext,
            "{\"id\":%d,\"ecg\":%d,\"bpm\":%d,\"ip\":\"%s\",\"rssi\":%ld}",
            compteur,
            ecgVal,
            bpmVal,
            WiFi.localIP().toString().c_str(),
            (long)WiFi.RSSI()
        );

       
        Serial.printf("[%5d] ECG=%4d BPM=%3d  %s\n", 
                     compteur, ecgVal, bpmVal,
                     ecg_state.electrode_loose ? " ELECTRODE_LOOSE" : 
                     (ecg_state.muscle_artifact_level > 0 ? "EMG" : "True"));

        
        publishEncrypted(topic_pub, plaintext);
    }
}
