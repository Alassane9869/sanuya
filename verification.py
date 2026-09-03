# verification.py
# Vérification des doublons par GPS (distance < 50 mètres)

import math

def distance_gps(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en mètres entre deux points GPS
    """
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    
    R = 6371000  # Rayon de la Terre en mètres
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def est_doublon(nouveau_lat, nouveau_lon, signalements_existants, seuil=50):
    """
    Vérifie si un nouveau signalement est un doublon
    Retourne : (est_doublon, id_doublon, distance)
    """
    nouveau_lat = float(nouveau_lat)
    nouveau_lon = float(nouveau_lon)
    
    for s in signalements_existants:
        if s.get('statut') in ['en_attente', 'en_cours']:
            distance = distance_gps(
                nouveau_lat, nouveau_lon,
                float(s['latitude']), float(s['longitude'])
            )
            
            if distance <= seuil:
                return True, s['id'], distance
    
    return False, None, None

# --- TEST ---
if __name__ == "__main__":
    print("🔍 Test de vérification des doublons")
    print("-" * 40)
    
    # Test 1 : Points proches
    lat1, lon1 = 12.6392, -8.0029
    lat2, lon2 = 12.6393, -8.0028
    
    dist = distance_gps(lat1, lon1, lat2, lon2)
    print(f"1. Distance : {dist:.1f} mètres")
    print(f"   {'✅ Doublon' if dist < 50 else '❌ Pas un doublon'}")
    
    # Test 2 : Points éloignés
    lat1, lon1 = 12.6392, -8.0029
    lat2, lon2 = 12.6500, -8.0100
    
    dist = distance_gps(lat1, lon1, lat2, lon2)
    print(f"2. Distance : {dist:.1f} mètres")
    print(f"   {'✅ Doublon' if dist < 50 else '❌ Pas un doublon'}")