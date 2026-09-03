# convertir_annotations.py
# Convertir le CSV en fichiers YOLO

import os
import csv

# 1. Lire le fichier CSV
csv_chemin = "labels_depot2.csv"

if not os.path.exists(csv_chemin):
    print(f"❌ Fichier {csv_chemin} introuvable")
    print("   Mets le fichier CSV dans le dossier du projet")
    exit()

# 2. Lire le CSV
annotations = []
with open(csv_chemin, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:
            nom_image = row[0].strip()
            labels = row[1].strip()
            annotations.append({
                'image': nom_image,
                'labels': labels
            })

print(f"📊 {len(annotations)} annotations trouvées")

# 3. Créer les fichiers .txt pour YOLO
for ann in annotations:
    nom_image = ann['image']
    nom_txt = nom_image.replace('.jpg', '.txt').replace('.jpeg', '.txt').replace('.png', '.txt')
    
    chemin_txt = os.path.join('dataset/labels/train', nom_txt)
    
    # Pour YOLO, on met une boîte au centre de l'image
    # class 0 = depot
    x_center = 0.5
    y_center = 0.5
    width = 0.8
    height = 0.8
    
    # Écrire le fichier .txt
    with open(chemin_txt, 'w') as f:
        f.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    print(f"✅ {nom_txt} créé")

print("\n✅ Conversion terminée !")
print(f"   {len(annotations)} fichiers .txt créés")
print("   Vérifie dans dataset/labels/train/")