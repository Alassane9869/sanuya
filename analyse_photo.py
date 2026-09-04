# analyse_photo.py
# Analyse de photo avec détection YOLO et GPS automatique

import os
import cv2
from ultralytics import YOLO
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from database import get_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 1. Charger le modèle ---
print("[INFO] Chargement du modèle YOLO...")

modele_paths = [
    os.path.join(BASE_DIR, "runs", "detect", "train", "weights", "best.pt"),
    os.path.join(BASE_DIR, "runs", "detect", "train-2", "weights", "best.pt"),
    os.path.join(BASE_DIR, "yolov8m.pt"),
    os.path.join(BASE_DIR, "yolov8n.pt")
]

modele = None
for path in modele_paths:
    if os.path.exists(path):
        print(f"[OK] Modèle trouvé : {path}")
        modele = YOLO(path)
        break

if modele is None:
    print("[ERREUR] Aucun modèle trouvé !")
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
        
        lat_data = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef', 'N')
        lon_data = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef', 'E')
        
        if not lat_data or not lon_data:
            return None
        
        def convertir_dms(valeur):
            d = float(valeur[0])
            m = float(valeur[1])
            s = float(valeur[2])
            return d + (m / 60.0) + (s / 3600.0)
        
        latitude = convertir_dms(lat_data)
        if lat_ref == 'S':
            latitude = -latitude
        
        longitude = convertir_dms(lon_data)
        if lon_ref == 'W':
            longitude = -longitude
        
        return {'latitude': latitude, 'longitude': longitude}
    except Exception as e:
        print(f"[AVERTISSEMENT] Erreur GPS : {e}")
        return None

# --- 3. Analyser la photo avec YOLO ---
def analyser_photo(chemin_photo):
    """Détecte les déchets et estime le volume"""
    img = cv2.imread(chemin_photo)
    if img is None:
        return None
    
    img_h, img_w = img.shape[:2]
    resultats = modele.predict(chemin_photo, conf=0.3, verbose=False)
    
    dechets = []
    for box in resultats[0].boxes:
        nom = modele.names[int(box.cls[0])]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        largeur = x2 - x1
        hauteur = y2 - y1
        
        dechets.append({
            'type': nom,
            'confiance': round(conf * 100, 1),
            'largeur': largeur,
            'hauteur': hauteur
        })
    
    if dechets:
        surface_relative = sum(d['largeur'] * d['hauteur'] for d in dechets) / (img_w * img_h)
        volume = max(0.1, round(surface_relative * 15.0, 2))
        
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
            'confiance_max': max(d['confiance'] for d in dechets)
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
    conn = get_connection()
    if conn is None:
        print("[ERREUR] Impossible de se connecter à la base de données")
        return False
    try:
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
        print(f"[ERREUR] Échec de sauvegarde : {e}")
        return False

# --- 5. Programme principal ---
def main():
    print("\n" + "="*50)
    print("SANUYA - Analyse de photo (GPS automatique)")
    print("="*50)
    
    chemin = input("Entrez le chemin de la photo : ").strip()
    if not os.path.exists(chemin):
        print(f"[ERREUR] Photo introuvable : {chemin}")
        return
    
    print("[INFO] Récupération de la position GPS...")
    gps = get_gps_from_exif(chemin)
    
    if gps:
        lat = gps['latitude']
        lon = gps['longitude']
        print(f"[OK] GPS trouvé : {lat:.6f}, {lon:.6f}")
    else:
        lat = 12.6392
        lon = -8.0029
        print(f"[AVERTISSEMENT] GPS non trouvé, position par défaut (Bamako) : {lat:.6f}, {lon:.6f}")
    
    print(f"\n[INFO] Analyse de : {chemin}")
    resultat = analyser_photo(chemin)
    
    print("\n" + "="*50)
    print("RÉSULTAT DE L'ANALYSE")
    print("="*50)
    
    if resultat and resultat['nb_dechets'] > 0:
        print(f"[OK] {resultat['nb_dechets']} déchet(s) détecté(s)")
        for d in resultat['dechets']:
            print(f"   - {d['type']} ({d['confiance']}%)")
        
        print(f"\nVolume estimé : {resultat['volume']} m³")
        print(f"Priorité      : {resultat['priorite'].upper()}")
        
        photo_nom = os.path.basename(chemin)
        if sauvegarder_db(lat, lon, resultat['volume'], resultat['priorite'], 'en_attente', photo_nom, chemin):
            print("[OK] Enregistré dans la base de données SANUYA")
    else:
        print("[INFO] Aucun déchet détecté sur cette photo.")

if __name__ == "__main__":
    main()