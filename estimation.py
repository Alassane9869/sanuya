# estimation.py
# Estimation du volume et priorisation des dépôts de déchets

def estimer_volume(largeur, hauteur, img_largeur=None, img_hauteur=None):
    """
    Estime le volume du dépôt (en m³) à partir de la boîte englobante.
    Si les dimensions totales de l'image sont fournies, le calcul est normalisé
    par rapport à la résolution de la caméra (indépendant de 4K, 1080p, etc.).
    """
    if img_largeur and img_hauteur and img_largeur > 0 and img_hauteur > 0:
        # Ratio de surface occupée par le dépôt dans l'image
        surface_relative = (largeur * hauteur) / (img_largeur * img_hauteur)
        # Étalonnage : une photo plein cadre représente environ 15 m³ de volume visible moyen
        volume_m3 = surface_relative * 15.0
    else:
        # Fallback si dimensions d'image non spécifiées
        volume_m3 = (largeur * hauteur) / 50000.0

    return max(0.05, round(volume_m3, 2))


def prioriser(volume):
    """
    Détermine le niveau d'urgence en fonction du volume estimé (en m³).
    - Urgent : > 5 m³ (obstruction majeure, risque sanitaire élevé)
    - Moyen  : entre 2 et 5 m³
    - Normal : < 2 m³ (dépôt diffus ou faible)
    """
    try:
        vol = float(volume)
    except (ValueError, TypeError):
        return "normal"

    if vol > 5.0:
        return "urgent"   # Rouge
    elif vol > 2.0:
        return "moyen"    # Orange
    else:
        return "normal"   # Vert


def traiter_detection(detection, img_largeur=None, img_hauteur=None):
    """
    Enrichit une détection avec son volume estimé et son niveau de priorité.
    """
    largeur = detection.get('largeur', 0)
    hauteur = detection.get('hauteur', 0)

    volume = estimer_volume(largeur, hauteur, img_largeur, img_hauteur)
    priorite = prioriser(volume)

    detection['volume'] = volume
    detection['priorite'] = priorite

    return detection


# --- TEST ---
if __name__ == "__main__":
    print("Test d'estimation de volume et priorisation")
    print("-" * 45)

    # Test avec résolution 1920x1080
    test_det = {'type': 'depot', 'confiance': 98.7, 'largeur': 600, 'hauteur': 400}
    res = traiter_detection(test_det, img_largeur=1920, img_hauteur=1080)
    print(f"Boîte 600x400 sur image 1920x1080 :")
    print(f"  Volume estimé : {res['volume']} m³")
    print(f"  Priorité      : {res['priorite']}")