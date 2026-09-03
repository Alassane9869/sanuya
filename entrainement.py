# entrainement.py
# Entraînement du modèle YOLO

from ultralytics import YOLO

print("🚀 Chargement du modèle...")
modele = YOLO('yolov8n.pt')

print("🏋️ Début de l'entraînement...")
modele.train(
    data='data.yaml',
    epochs=50,
    imgsz=640,
    batch=4,
    patience=20
)

print("✅ Entraînement terminé !")
print("📁 Modèle sauvegardé dans runs/detect/train/weights/best.pt")