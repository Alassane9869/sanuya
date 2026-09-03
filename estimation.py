# estimation.py
# Estimation du volume et priorité

def estimer_volume(largeur, hauteur):
    """
    Estime le volume du dépôt à partir de la taille de la boîte
    """
    # Surface en pixels
    surface = largeur * hauteur
    
    # Conversion en m² (approximation)
    # On suppose qu'un dépôt de 1000 pixels² ≈ 1 m²
    surface_m2 = surface / 1000
    
    # Volume estimé (en m³)
    # On suppose une hauteur moyenne de 0.5 m
    volume_m3 = surface_m2 * 0.5
    
    return round(volume_m3, 2)

def prioriser(volume):
    """
    Détermine la priorité en fonction du volume
    """
    if volume > 5:
        return "urgent"   # 🔴 Rouge
    elif volume > 2:
        return "moyen"    # 🟠 Orange
    else:
        return "normal"   # 🟢 Vert

def traiter_detection(detection):
    """
    Ajoute le volume et la priorité à une détection
    """
    largeur = detection.get('largeur', 0)
    hauteur = detection.get('hauteur', 0)
    
    volume = estimer_volume(largeur, hauteur)
    priorite = prioriser(volume)
    
    detection['volume'] = volume
    detection['priorite'] = priorite
    
    return detection

# --- TEST ---
if __name__ == "__main__":
    # Simuler une détection
    detection = {
        'type': 'depot',
        'confiance': 98.7,
        'largeur': 300,
        'hauteur': 200
    }
    
    print("🔍 Test d'estimation")
    print("-" * 40)
    print(f"Largeur: {detection['largeur']} px")
    print(f"Hauteur: {detection['hauteur']} px")
    
    resultat = traiter_detection(detection)
    
    print(f"📦 Volume estimé: {resultat['volume']} m³")
    print(f"🚨 Priorité: {resultat['priorite']}")