# carte.py
# Carte interactive avec Folium

import folium
import os
import json

def creer_carte(donnees_depots, fichier_sortie="carte_depots.html"):
    """
    Crée une carte interactive avec les dépôts
    """
    # Centrer sur Bamako
    carte = folium.Map(location=[12.6392, -8.0029], zoom_start=13)
    
    # Couleurs selon priorité
    couleurs = {
        'urgent': 'red',
        'moyen': 'orange',
        'normal': 'green'
    }
    
    # Ajouter les dépôts sur la carte
    for depot in donnees_depots:
        couleur = couleurs.get(depot.get('priorite', 'normal'), 'blue')
        
        # Message popup
        popup = f"""
        <b>Dépôt</b><br>
        📦 Volume: {depot.get('volume', '?')} m³<br>
        🚨 Priorité: {depot.get('priorite', 'inconnue')}<br>
        📍 Position: {depot.get('latitude', '?')}, {depot.get('longitude', '?')}
        """
        
        # Ajouter le marqueur
        folium.Marker(
            location=[depot['latitude'], depot['longitude']],
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(color=couleur, icon='trash', prefix='fa')
        ).add_to(carte)
    
    # Ajouter une légende
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background: white; padding: 12px; border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <div><span style="color:red;">●</span> Urgent (volume > 5 m³)</div>
        <div><span style="color:orange;">●</span> Moyen (volume 2-5 m³)</div>
        <div><span style="color:green;">●</span> Normal (volume < 2 m³)</div>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(legend_html))
    
    # Sauvegarder
    carte.save(fichier_sortie)
    print(f"✅ Carte sauvegardée : {fichier_sortie}")
    return carte

# --- TEST AVEC DONNÉES EXEMPLE ---
if __name__ == "__main__":
    # Données fictives pour le test
    depots_test = [
        {'latitude': 12.6392, 'longitude': -8.0029, 'volume': 8.5, 'priorite': 'urgent'},
        {'latitude': 12.6450, 'longitude': -8.0150, 'volume': 3.2, 'priorite': 'moyen'},
        {'latitude': 12.6300, 'longitude': -7.9950, 'volume': 1.1, 'priorite': 'normal'},
        {'latitude': 12.6500, 'longitude': -8.0100, 'volume': 6.7, 'priorite': 'urgent'},
        {'latitude': 12.6350, 'longitude': -8.0050, 'volume': 2.5, 'priorite': 'moyen'},
    ]
    
    print("🗺️ Création de la carte de test")
    print("-" * 40)
    print(f"📍 {len(depots_test)} dépôts à afficher")
    
    creer_carte(depots_test, "carte_test.html")
    print("\n📁 Ouvre 'carte_test.html' dans ton navigateur")