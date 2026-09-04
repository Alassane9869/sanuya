# tester.py
# Tester le modèle YOLO de détection de dépôts sauvages

from ultralytics import YOLO
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemins possibles pour le modèle (du plus spécialisé au modèle par défaut)
model_candidates = [
    os.path.join(BASE_DIR, "runs", "detect", "train", "weights", "best.pt"),
    os.path.join(BASE_DIR, "runs", "detect", "train-2", "weights", "best.pt"),
    os.path.join(BASE_DIR, "yolov8m.pt"),
    os.path.join(BASE_DIR, "yolov8n.pt")
]

model_path = next((p for p in model_candidates if os.path.exists(p)), "yolov8n.pt")
print(f"[INFO] Chargement du modèle : {model_path}")
modele = YOLO(model_path)

# Image de test
chemin = os.path.join(BASE_DIR, "images_brutes", "test.jpg")
if not os.path.exists(chemin):
    # Trouver une image de secours dans images_test ou images_brutes
    test_dir = os.path.join(BASE_DIR, "images_test")
    if os.path.exists(test_dir):
        imgs = [os.path.join(test_dir, f) for f in os.listdir(test_dir) if f.lower().endswith(('.jpg', '.png'))]
        if imgs:
            chemin = imgs[0]

if os.path.exists(chemin):
    print(f"[INFO] Analyse de : {chemin}")
    resultats = modele.predict(chemin, conf=0.3, save=True)
    
    for r in resultats:
        if len(r.boxes) > 0:
            print(f"[OK] {len(r.boxes)} dépôt(s) détecté(s)")
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_name = modele.names[int(box.cls[0])]
                print(f"   - {cls_name} : ({x1}, {y1}) à ({x2}, {y2}) - Confiance : {conf*100:.1f}%")
        else:
            print("[INFO] Aucun dépôt détecté")
    
    print("[INFO] Résultat sauvegardé dans runs/detect/predict/")
else:
    print(f"[AVERTISSEMENT] Aucune image trouvée pour le test.")