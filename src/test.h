#ifndef TEST_H
#define TEST_H

#include <Arduino.h>

// 1. PINS DU CAPTEUR AD8232

const int ecgSignalPin = 32;    
const int loPositivePin = 19;   
const int loNegativePin = 18;   

// 2. VARIABLES DU FILTRE ET DE L'AFFICHAGE

const float alpha = 0.4; 
float filteredECG = 2000.0;
bool leadsOff = false;
int printCounter = 0; // Compteur pour ralentir l'affichage Série


// 3. VARIABLES POUR LE CALCUL DU RYTHME CARDIAQUE (BPM)

unsigned long lastBeatTime = 0;
int currentBPM = 0;

// /!\ SEUIL IMPORTANT  Dès que la courbe dépasse 2300, on compte un battement.
const int threshold = 2300; 
bool beatDetected = false;

// 4. INITIALISATION DU CAPTEUR

void setupECG() {
    pinMode(ecgSignalPin, INPUT);
    pinMode(loPositivePin, INPUT);
    pinMode(loNegativePin, INPUT);
}

// 5. FONCTION PRINCIPALE (Appelée toutes les 4ms par main.cpp)

void updateECG() {
    int lo_plus = digitalRead(loPositivePin);
    int lo_minus = digitalRead(loNegativePin);
    leadsOff = (lo_plus == 1 || lo_minus == 1);

    if (leadsOff) {
        filteredECG = 2000.0; 
        currentBPM = 0; // Si débranché, le rythme tombe à 0
    } 
    else {
        int rawECG = analogRead(ecgSignalPin);
        
        //  Application du filtre
        filteredECG = (alpha * rawECG) + ((1.0 - alpha) * filteredECG);

        //  Calcul du Rythme Cardiaque (BPM)
        unsigned long currentTime = millis();
        
        // Si la courbe franchit le seuil vers le haut = C'est un pic !
        if (filteredECG > threshold && !beatDetected) {
            beatDetected = true;
            
            // Calcul du temps écoulé depuis le dernier battement
            unsigned long timeBetweenBeats = currentTime - lastBeatTime;
            
            // Un cœur humain bat entre 60 et 100 BPM (soit 600ms à 1000ms entre 2 battements)
            // On vérifie que c'est bien un vrai battement et pas une erreur
            if (timeBetweenBeats >= 600 && timeBetweenBeats <= 1000) {
                currentBPM = 60000 / timeBetweenBeats; // Formule magique des BPM
            }
            lastBeatTime = currentTime;
        }
        
        // Si la courbe redescend, on réarme le détecteur pour le prochain battement
        if (filteredECG < (threshold - 100)) {
            beatDetected = false;
        }
    }

    // 5c. Affichage pour le Traceur Série 
    // On envoie les données 1 fois sur 3 pour accumuler la courbe à l'écran
    printCounter++;
    if (printCounter >= 3) {
        Serial.print("Min:1000,");      
        Serial.print("Max:3000,");      
        Serial.print("ECG:");           
        Serial.print(filteredECG);
        Serial.print(",");
        Serial.print("BPM:");           
        Serial.println(currentBPM); // Affiche le rythme cardiaque sur le graphique !
        
        printCounter = 0;
    }
}

// 6. FONCTIONS POUR ENVOYER LES DONNÉES À MAIN.CPP (MQTT)

int getECGValue() {
    return (int)filteredECG;
}

int getBPMValue() {
    return currentBPM;
}

#endif