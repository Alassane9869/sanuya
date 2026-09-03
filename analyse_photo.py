# analyse_photo_auto.py
# Analyse de photo avec GPS automatique

import os
import cv2
from ultralytics import YOLO
import mysql.connector
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# --- Configuration ---
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '27142005',
    'database': 'sanuya'
}

# --- 1. Charger le modèle ---
print("🔍 Chargement du modèle YOLO...")

modele_paths = [
    'runs/detect/train-2/weights/best.pt',
    'C:/Users/hp/runs/detect/train-2/weights/best.pt',
    'yolov8n.pt'
]

modele = None
for path in modele_paths:
    if os.path.exists(path):
        print(f"✅ Modèle trouvé : {path}")
        modele = YOLO(path)
        break

if modele is None:
    print("❌ Aucun modèle trouvé !")
    exit()

# --- 2. Fonction pour récupérer le GPS depuis EXIF ---
def get_gps_from_exif(chemin_photo):
    """Récupère les coordonnées GPS depuis les métadonnées EXIF de la photo"""
    try:
        image = Image.open(chemin_photo)
        exifdata = image.getexif()
        
        if not exifdata:
            return None
        
        gps_info = {}
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value
        
        if not gps_info:
            return None
        
        # Convertir les coordonnées en degrés décimaux
        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        
        lat = convert_to_degrees(gps_info['GPSLatitude'])
        lon = convert_to_degrees(gps_info['GPSLongitude'])
        
        # Gestion des signes (Nord/Sud, Est/Ouest)
        if gps_info['GPSLatitudeRef'] == 'S':
            lat = -lat
        if gps_info['GPSLongitudeRef'] == 'W':
            lon = -lon
        
        return {'latitude': lat, 'longitude': lon}
    except Exception as e:
        print(f"⚠️ Erreur lecture GPS : {e}")
        return None

# --- 3. Fonction d'analyse ---
def analyser_photo(chemin_photo):
    """Analyse une photo avec YOLO"""
    if not os.path.exists(chemin_photo):
        return {'erreur': 'Fichier introuvable'}
    
    image = cv2.imread(chemin_photo)
    if image is None:
        return {'erreur': 'Image invalide'}
    
    resultats = modele.predict(image, conf=0.3, verbose=False)
    
    dechets = []
    for r in resultats:
        for box in r.boxes:
            nom = modele.names[int(box.cls[0])]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            
            dechets.append({
                'type': nom,
                'confiance': round(conf * 100, 2),
                'largeur': x2 - x1,
                'hauteur': y2 - y1
            })
    
    if dechets:
        volume = sum(d['largeur'] * d['hauteur'] for d in dechets) / 100000
        volume = round(volume, 2)
        
        if volume > 5:
            priorite = 'urgent'
        elif volume > 2:
            priorite = 'moyen'
        else:
            priorite = 'normal'
        
        return {
            'nb_dechets': len(dechets),
            'dechets': dechets,
            'volume': volume,
            'priorite': priorite,
            'confiance_max': max([d['confiance'] for d in dechets])
        }
    else:
        return {
            'nb_dechets': 0,
            'dechets': [],
            'volume': 0,
            'priorite': 'normal',
            'confiance_max': 0
        }

# --- 4. Fonction de sauvegarde ---
def sauvegarder_db(lat, lon, volume, priorite, statut, photo_nom, photo_chemin):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signalements 
            (latitude, longitude, volume, priorite, statut, date_creation, photo_nom, photo_chemin)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
        """, (lat, lon, volume, priorite, statut, photo_nom, photo_chemin))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur MySQL : {e}")
        return False

# --- 5. Programme principal ---
def main():
    print("\n" + "="*50)
    print("🗑️ SANUYA - Analyse de photo (GPS automatique)")
    print("="*50)
    
    # Demander le chemin de la photo
    chemin = input("📸 Entrez le chemin de la photo : ")
    
    if not os.path.exists(chemin):
        print(f"❌ Photo introuvable : {chemin}")
        return
    
    # Récupérer le GPS depuis EXIF
    print("📍 Récupération de la position GPS...")
    gps = get_gps_from_exif(chemin)
    
    if gps:
        lat = gps['latitude']
        lon = gps['longitude']
        print(f"✅ GPS trouvé : {lat:.6f}, {lon:.6f}")
    else:
        # Position par défaut (Bamako)
        lat = 12.6392
        lon = -8.0029
        print(f"⚠️ GPS non trouvé, position par défaut : {lat:.6f}, {lon:.6f}")
    
    # Analyser
    print(f"\n🔍 Analyse de : {chemin}")
    resultat = analyser_photo(chemin)
    
    # Afficher les résultats
    print("\n" + "="*50)
    print("📊 RÉSULTAT DE L'ANALYSE")
    print("="*50)
    
    if resultat['nb_dechets'] > 0:
        print(f"✅ {resultat['nb_dechets']} déchet(s) détecté(s)")
        for d in resultat['dechets']:
            print(f"   - {d['type']} (confiance: {d['confiance']}%)")
        print(f"\n📦 Volume estimé : {resultat['volume']} m³")
        print(f"🚨 Priorité : {resultat['priorite'].upper()}")
        print(f"🎯 Confiance max : {resultat['confiance_max']}%")
        print(f"📍 Position : {lat:.6f}, {lon:.6f}")
        
        # Sauvegarder
        print("\n💾 Sauvegarde dans MySQL...")
        nom_fichier = os.path.basename(chemin)
        success = sauvegarder_db(
            lat, lon,
            resultat['volume'],
            resultat['priorite'],
            'en_attente',
            nom_fichier,
            chemin
        )
        
        if success:
            print("✅ Dépôt sauvegardé dans la base de données")
        else:
            print("❌ Erreur de sauvegarde")
    else:
        print("❌ Aucun déchet détecté sur cette photo")
    
    print("\n" + "="*50)
    print("✅ Analyse terminée")

# --- Lancer le programme ---
if __name__ == "__main__":
    main()