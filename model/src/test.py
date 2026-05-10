import joblib

# Chemin du fichier à tester
chemin_fichier = 'model/models/scaler.pkl'

try:
    # Charger le fichier binaire
    objet_charge = joblib.load(chemin_fichier)
    
    print("Fichier chargé avec succès !")
    print("Type de l'objet :", type(objet_charge))
    print("Contenu :", objet_charge)
    
except Exception as e:
    print(f"Erreur lors du chargement : {e}")