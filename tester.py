# tester.py
# Tester le modèle entraîné

from ultralytics import YOLO
import os

# Charger le modèle
modele = YOLO('C:/Users/hp/runs/detect/train-2/weights/best.pt')

# Chemin relatif
chemin = "images_brutes/test.jpg"

if os.path.exists(chemin):
    print(f"🔍 Analyse de : {chemin}")
    resultats = modele.predict(chemin, conf=0.3, save=True)
    
    for r in resultats:
        if len(r.boxes) > 0:
            print(f"✅ {len(r.boxes)} dépôt(s) détecté(s)")
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                print(f"   - Boîte : ({x1}, {y1}) à ({x2}, {y2}) - Confiance : {conf*100:.1f}%")
        else:
            print("❌ Aucun dépôt détecté")
    
    print("📁 Résultat sauvegardé dans runs/detect/predict/")
else:
    print(f"❌ Image introuvable : {chemin}")
    print("   Vérifie que l'image existe dans images_brutes/")