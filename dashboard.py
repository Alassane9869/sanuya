import dash
from dash import dcc, html, Input, Output, State, dash_table, MATCH, ALL
import dash_bootstrap_components as dbc
import mysql.connector
from datetime import datetime, date, timedelta
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import os
import cv2
import base64
from ultralytics import YOLO
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim
import time
import json
import requests

# ----- Configuration Dash -----
app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="SANUYA - Dashboard"
)

server = app.server
#--- Style ---
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { font-family: 'Inter', sans-serif; }
            body { background: #f0f4f8; }
            
            .sidebar-link {
                transition: all 0.2s ease;
                color: #94a3b8 !important;
                font-weight: 500;
            }
            .sidebar-link:hover {
                background: rgba(255,255,255,0.05);
                color: #ffffff !important;
            }
            .sidebar-link.active {
                background: rgba(255,255,255,0.08);
                color: #ffffff !important;
                border-right: 3px solid #00d4ff;
            }
            .sidebar-link i { width: 20px; text-align: center; }
            
            .page-title {
                font-weight: 700;
                color: #0f172a;
                font-size: 28px;
                letter-spacing: -0.5px;
            }
            .page-subtitle {
                color: #64748b;
                font-size: 15px;
                margin-top: 4px;
            }
            
            .stat-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 20px 24px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                border: 1px solid #e9edf2;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                position: relative;
                overflow: hidden;
            }
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            }
            .stat-card .number {
                font-size: 32px;
                font-weight: 700;
                letter-spacing: -0.5px;
                margin-bottom: 2px;
            }
            .stat-card .label {
                font-size: 14px;
                color: #64748b;
                font-weight: 500;
            }
            .stat-card .icon {
                position: absolute;
                right: 20px;
                top: 20px;
                font-size: 28px;
                opacity: 0.15;
            }
            .stat-card .glow {
                position: absolute;
                top: -50%;
                right: -50%;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                opacity: 0.03;
                pointer-events: none;
            }
            .glow-blue { background: radial-gradient(circle, #3b82f6 0%, transparent 70%); }
            .glow-red { background: radial-gradient(circle, #ef4444 0%, transparent 70%); }
            .glow-orange { background: radial-gradient(circle, #f59e0b 0%, transparent 70%); }
            .glow-green { background: radial-gradient(circle, #22c55e 0%, transparent 70%); }

            .content-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                border: 1px solid #e9edf2;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            .stats-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            .map-container {
                height: 600px;
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid #e9edf2;
            }
            .map-container iframe {
                width: 100%;
                height: 100%;
                border: none;
            }
            .legend {
                display: flex;
                gap: 20px;
                padding: 12px 16px;
                background: #f8fafc;
                border-radius: 10px;
                border: 1px solid #e9edf2;
                margin-top: 12px;
                flex-wrap: wrap;
            }
            .legend-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 13px;
                color: #475569;
            }
            .legend-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }
            
            .upload-area {
                border: 2px dashed #e9edf2;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: 0.3s;
            }
            .upload-area:hover {
                border-color: #00d4ff;
                background: #f8fafc;
            }
            .upload-area i {
                font-size: 48px;
                color: #94a3b8;
            }
            
            .filter-section {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                margin-bottom: 16px;
                padding: 16px;
                background: #f8fafc;
                border-radius: 12px;
                align-items: flex-end;
            }
            .filter-group {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .filter-group label {
                font-size: 13px;
                color: #64748b;
                font-weight: 500;
            }
            .filter-group .dash-dropdown {
                min-width: 160px;
            }
            
            .depot-card {
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 8px;
                border: 1px solid #e9edf2;
                transition: all 0.2s ease;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }
            .depot-card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.06);
                border-color: #00d4ff;
            }
            .depot-card .depot-info {
                display: flex;
                align-items: center;
                gap: 16px;
                flex-wrap: wrap;
            }
            .depot-card .depot-id {
                font-weight: 700;
                font-size: 16px;
                color: #0f172a;
                min-width: 60px;
            }
            .depot-card .depot-date {
                font-size: 13px;
                color: #64748b;
            }
            .depot-card .depot-volume {
                font-weight: 600;
                color: #0f172a;
            }
            .depot-card .badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }
            .depot-card .depot-actions {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
            }
            .depot-card .action-btn {
                padding: 4px 12px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: 0.2s;
            }
            .depot-card .action-btn:hover { opacity: 0.8; transform: scale(1.02); }
            .btn-status { background: #fffbeb; color: #f59e0b; }
            .btn-priorite { background: #f0fdf4; color: #22c55e; }
            .btn-delete { background: #fef2f2; color: #ef4444; }
            .btn-photo { background: #eff6ff; color: #3b82f6; }
            .btn-maps { background: #e8f5e9; color: #2e7d32; }
            
            .badge-urgent { background: #fef2f2; color: #ef4444; }
            .badge-moyen { background: #fffbeb; color: #f59e0b; }
            .badge-normal { background: #f0fdf4; color: #22c55e; }
            .badge-attente { background: #fffbeb; color: #f59e0b; }
            .badge-cours { background: #eff6ff; color: #3b82f6; }
            .badge-resolu { background: #f0fdf4; color: #22c55e; }
            
            .stats-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .stats-container .card {
                margin-bottom: 0;
            }
            
            @media (max-width: 768px) {
                .stats-container { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# --- Chargement du modèle YOLO ---
def load_model():
    paths = [
        'runs/detect/train-2/weights/best.pt',
        'C:/Users/hp/runs/detect/train-2/weights/best.pt',
        'yolov8n.pt'
    ]
    for p in paths:
        if os.path.exists(p):
            print(f"✅ Modèle chargé : {p}")
            return YOLO(p)
    print("⚠️ Modèle par défaut")
    return YOLO('yolov8n.pt')

model = load_model()

# --- Connexion MySQL ---
def get_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='27142005',
            database='sanuya'
        )
    except Exception as e:
        print(f"❌ MySQL : {e}")
        return None

# --- Fonctions d'extraction de métadonnées ---
def get_location_from_metadata(chemin_photo):
    try:
        image = Image.open(chemin_photo)
        exifdata = image.getexif()
        if not exifdata:
            return None
        
        location_info = []
        
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            
            if tag in ['XPComment', 'XPSubject', 'XPKeywords', 'XPTitle', 'ImageDescription', 'Make', 'Model']:
                if isinstance(value, bytes):
                    try:
                        for encoding in ['utf-16le', 'utf-8', 'latin1']:
                            try:
                                decoded = value.decode(encoding, errors='ignore').strip('\x00')
                                if decoded and len(decoded) > 2 and not decoded.startswith('Android'):
                                    location_info.append(decoded)
                                    break
                            except:
                                continue
                    except:
                        pass
                elif isinstance(value, str) and len(value) > 2:
                    location_info.append(value)
        
        if location_info:
            for info in location_info:
                if info and len(info) > 2 and not any(x in info.lower() for x in ['android', 'iphone', 'camera']):
                    return f"Lieu détecté: {info}"
        return None
    except Exception as e:
        print(f"⚠️ Erreur extraction lieu: {e}")
        return None

def get_gps_from_filename(chemin_photo):
    filename = os.path.basename(chemin_photo)
    if 'IMG' in filename and '_' in filename:
        parts = filename.split('_')
        if len(parts) >= 2:
            date_part = parts[1]
            if len(date_part) >= 14:
                try:
                    year = int(date_part[0:4])
                    month = int(date_part[4:6])
                    day = int(date_part[6:8])
                    hour = int(date_part[9:11]) if len(date_part) > 11 else 0
                    minute = int(date_part[11:13]) if len(date_part) > 13 else 0
                    return f"Prise le {day:02d}/{month:02d}/{year} à {hour:02d}h{minute:02d}"
                except:
                    pass
    return None

def get_all_exif_tags(chemin_photo):
    try:
        image = Image.open(chemin_photo)
        exifdata = image.getexif()
        if not exifdata:
            return {}
        
        tags = {}
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='ignore')
                except:
                    value = str(value)
            tags[tag] = value
        return tags
    except Exception as e:
        print(f"⚠️ Erreur tags EXIF: {e}")
        return {}

def search_coordinates_by_name(location_name):
    if not location_name or len(location_name) < 3:
        return None
    
    try:
        geolocator = Nominatim(user_agent="sanuya_app", timeout=5)
        location_name = location_name.replace('Lieu détecté: ', '').strip()
        
        search_terms = [
            location_name,
            f"{location_name}, Mali",
            f"{location_name}, Bamako, Mali"
        ]
        
        for term in search_terms:
            try:
                location = geolocator.geocode(term, language='fr')
                if location:
                    return {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'address': location.address
                    }
            except:
                continue
        
        return None
    except Exception as e:
        print(f"⚠️ Erreur recherche coordonnées: {e}")
        return None

# --- Récuperation du gps ---
def get_gps_from_exif(chemin_photo):
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
        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        lat = convert_to_degrees(gps_info['GPSLatitude'])
        lon = convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLatitudeRef'] == 'S':
            lat = -lat
        if gps_info['GPSLongitudeRef'] == 'W':
            lon = -lon
        return {'latitude': lat, 'longitude': lon}
    except Exception as e:
        print(f"⚠️ Erreur lecture GPS : {e}")
        return None

def get_gps_precision(chemin_photo):
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
        precision = gps_info.get('GPSDOP', None)
        if precision:
            if isinstance(precision, tuple) and len(precision) >= 2:
                return float(precision[0]) / float(precision[1])
            elif isinstance(precision, (int, float)):
                return float(precision)
        return None
    except Exception as e:
        print(f"⚠️ Erreur précision GPS : {e}")
        return None

def get_capture_date(chemin_photo):
    try:
        image = Image.open(chemin_photo)
        exifdata = image.getexif()
        if not exifdata:
            return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                date_str = value
                try:
                    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    return dt.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    return date_str
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    except Exception as e:
        print(f"⚠️ Erreur date capture : {e}")
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ==================== STATS POUR LE TABLEAU DE BORD ====================
def get_stats_dashboard():
    conn = get_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut != 'resolu'")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE priorite = 'urgent' AND statut != 'resolu'")
        urgent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE priorite = 'moyen' AND statut != 'resolu'")
        moyen = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE priorite = 'normal' AND statut != 'resolu'")
        normal = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut = 'en_attente'")
        attente = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut = 'en_cours'")
        cours = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut = 'resolu'")
        resolu = cursor.fetchone()[0]
        
        conn.close()
        return {'total': total, 'urgent': urgent, 'moyen': moyen, 'normal': normal,
                'attente': attente, 'cours': cours, 'resolu': resolu}
    except Exception as e:
        print(f"❌ Erreur stats dashboard : {e}")
        return {}

def get_stats_complete():
    conn = get_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM signalements")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE priorite = 'urgent'")
        urgent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE priorite = 'moyen'")
        moyen = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE priorite = 'normal'")
        normal = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut = 'en_attente'")
        attente = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut = 'en_cours'")
        cours = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signalements WHERE statut = 'resolu'")
        resolu = cursor.fetchone()[0]
        
        conn.close()
        return {'total': total, 'urgent': urgent, 'moyen': moyen, 'normal': normal,
                'attente': attente, 'cours': cours, 'resolu': resolu}
    except Exception as e:
        print(f"❌ Erreur stats complètes : {e}")
        return {}

def get_depots_filtres(filtre_priorite='tous', filtre_statut='tous'):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT id, latitude, longitude, volume, priorite, statut, 
                   DATE_FORMAT(date_creation, '%d/%m/%Y %H:%i') as date,
                   photo_chemin
            FROM signalements 
            WHERE 1=1
        """
        params = []
        
        if filtre_statut == 'tous':
            query += " AND statut != 'resolu'"
        
        if filtre_priorite != 'tous':
            query += " AND priorite = %s"
            params.append(filtre_priorite)
        
        if filtre_statut != 'tous':
            query += " AND statut = %s"
            params.append(filtre_statut)
        
        query += " ORDER BY date_creation DESC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"❌ Erreur depots : {e}")
        return []

# ==================== FONCTIONS CRUD ====================
def add_detection(lat, lon, volume, priorite, statut, photo_nom):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signalements 
            (latitude, longitude, volume, priorite, statut, date_creation, photo_nom, photo_chemin)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
        """, (lat, lon, volume, priorite, statut, photo_nom, f"images_test/{photo_nom}"))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur ajout : {e}")
        return False

def update_status_db(depot_id, statut):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE signalements SET statut = %s WHERE id = %s", (statut, depot_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur mise à jour : {e}")
        return False

def update_priorite_db(depot_id, priorite):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE signalements SET priorite = %s WHERE id = %s", (priorite, depot_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur mise à jour : {e}")
        return False

def delete_depot_db(depot_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signalements WHERE id = %s", (depot_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur suppression : {e}")
        return False

# ==================== ANALYSE YOLO ====================
def analyser_photo(chemin):
    if not os.path.exists(chemin):
        return {'erreur': 'Fichier introuvable'}
    img = cv2.imread(chemin)
    if img is None:
        return {'erreur': 'Image invalide'}
    r = model.predict(img, conf=0.3, verbose=False)
    dechets = []
    for box in r[0].boxes:
        nom = model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        dechets.append({'type': nom, 'confiance': round(conf*100, 2), 'largeur': x2-x1, 'hauteur': y2-y1})
    if dechets:
        vol = round(sum(d['largeur']*d['hauteur'] for d in dechets) / 100000, 2)
        prio = determiner_priorite(vol)
        return {'nb': len(dechets), 'dechets': dechets, 'volume': vol, 'priorite': prio}
    return {'nb': 0, 'dechets': [], 'volume': 0, 'priorite': 'normal'}

# ==================== Generation de carte ====================
def generate_map():
    depots = get_depots_filtres()
    depots = [d for d in depots if d['statut'] != 'resolu']
    
    carte = folium.Map(
        location=[12.6392, -8.0029],
        zoom_start=13,
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; CartoDB'
    )
    
    if not depots:
        folium.Marker(
            location=[12.6392, -8.0029],
            popup="Aucun dépôt en attente",
            icon=folium.Icon(color='gray', icon='info', prefix='fa')
        ).add_to(carte)
        return carte._repr_html_()
    
    cluster = MarkerCluster().add_to(carte)
    couleurs = {'urgent': 'red', 'moyen': 'orange', 'normal': 'green'}
    
    for depot in depots:
        lat = float(depot['latitude'])
        lon = float(depot['longitude'])
        
        if abs(lat - 12.6392) < 0.0001 and abs(lon - (-8.0029)) < 0.0001:
            continue
        
        priorite = depot['priorite']
        statut = depot['statut']
        volume = depot['volume']
        depot_id = depot['id']
        couleur = couleurs.get(priorite, 'gray')
        
        adresse = get_address(lat, lon)
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        
        popup_text = f"""
        <b>Dépôt #{depot_id}</b><br>
        {adresse}<br>
        Volume: {volume} m³<br>
        Priorité: {priorite}<br>
        Statut: {statut}<br>
        <a href="{maps_link}" target="_blank" style="color:#007bff;font-weight:600;">Voir sur Google Maps</a>
        """
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=couleur, icon='trash', prefix='fa')
        ).add_to(cluster)
    
    return carte._repr_html_()

# ==================== SIDEBAR ====================
sidebar = html.Div([
    html.Div([
        html.Div([
            html.I(className="fas fa-trash-alt", style={'fontSize': '22px', 'color': '#00d4ff', 'marginRight': '14px'}),
            html.Span("SANUYA", style={'fontSize': '20px', 'fontWeight': '800', 'color': '#ffffff', 'letterSpacing': '-0.5px'})
        ], className="d-flex align-items-center px-3 py-4")
    ], style={'borderBottom': '1px solid rgba(255,255,255,0.06)'}),
    html.Div([
        html.P("MENU", className="text-uppercase text-white-50 px-3 mt-3 mb-2", style={'fontSize': '10px', 'fontWeight': '600', 'letterSpacing': '2px'}),
        dbc.Nav([
            dbc.NavLink([html.I(className="fas fa-chart-pie me-3"), html.Span("Tableau de bord")], href="/", active="exact", className="sidebar-link py-2 px-3 rounded-3"),
            dbc.NavLink([html.I(className="fas fa-list me-3"), html.Span("Liste des dépôts")], href="/liste", active="exact", className="sidebar-link py-2 px-3 rounded-3"),
            dbc.NavLink([html.I(className="fas fa-chart-line me-3"), html.Span("Statistiques")], href="/stats", active="exact", className="sidebar-link py-2 px-3 rounded-3"),
            dbc.NavLink([html.I(className="fas fa-camera me-3"), html.Span("Tester")], href="/tester", active="exact", className="sidebar-link py-2 px-3 rounded-3"),
        ], vertical=True, pills=False, className="px-2")
    ], className="mt-2"),
], style={
    'position': 'fixed', 'top': 0, 'left': 0, 'bottom': 0,
    'width': '230px', 'background': '#0f172a', 'padding': '0',
    'zIndex': '1000', 'display': 'flex', 'flexDirection': 'column'
})

# ==================== CONTENU ====================
content = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
    dcc.Interval(id="interval-stats", interval=5000)
], style={'marginLeft': '230px', 'padding': '30px', 'backgroundColor': '#f0f4f8', 'minHeight': '100vh'})

app.layout = html.Div([sidebar, content])

# ==================== STAT CARD ====================
def create_stat_card(title, value, color):
    glow_class = {'blue': 'glow-blue', 'red': 'glow-red', 'orange': 'glow-orange', 'green': 'glow-green'}.get(color, 'glow-blue')
    color_map = {'blue': '#3b82f6', 'red': '#ef4444', 'orange': '#f59e0b', 'green': '#22c55e'}
    return html.Div([
        html.Div(className=f"glow {glow_class}"),
        html.Div([
            html.Div(str(value), className="number", style={'color': color_map[color]}),
            html.Div(title, className="label")
        ])
    ], className="stat-card")

# ==================== PAGE TABLEAU DE BORD ====================
def page_dashboard():
    return html.Div([
        html.H1("Tableau de bord", className="page-title"),
        html.P("Statistiques des dépôts non résolus", className="page-subtitle mb-4"),
        html.Div(id="stats-container")
    ])

# ==================== PAGE LISTE ====================
def page_liste():
    return html.Div([
        html.H1("Liste des dépôts", className="page-title"),
        html.P("Gérez tous les signalements", className="page-subtitle mb-4"),
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Filtrer par priorité"),
                    dcc.Dropdown(
                        id="filtre-priorite",
                        options=[
                            {'label': 'Tous', 'value': 'tous'},
                            {'label': 'Urgent', 'value': 'urgent'},
                            {'label': 'Moyen', 'value': 'moyen'},
                            {'label': 'Normal', 'value': 'normal'}
                        ],
                        value='tous',
                        className="dash-dropdown"
                    )
                ], className="filter-group"),
                html.Div([
                    html.Label("Filtrer par statut"),
                    dcc.Dropdown(
                        id="filtre-statut",
                        options=[
                            {'label': 'Tous', 'value': 'tous'},
                            {'label': 'En attente', 'value': 'en_attente'},
                            {'label': 'En cours', 'value': 'en_cours'},
                            {'label': 'Résolu', 'value': 'resolu'}
                        ],
                        value='tous',
                        className="dash-dropdown"
                    )
                ], className="filter-group"),
                html.Div([
                    html.Label("Rechercher par ID"),
                    dcc.Input(
                        id="search-id",
                        type="number",
                        placeholder="ID du dépôt",
                        style={'padding': '8px 12px', 'borderRadius': '8px', 'border': '1px solid #e9edf2', 'width': '150px'}
                    )
                ], className="filter-group"),
                html.Div([
                    html.Label("Actions"),
                    html.Div([
                        dbc.Button("Appliquer", id="btn-apply-filters", color="primary", size="sm", className="me-2"),
                        dbc.Button("Reset", id="btn-reset-filters", color="secondary", size="sm")
                    ], style={'display': 'flex', 'gap': '8px'})
                ], className="filter-group")
            ], className="filter-section"),
            html.Div(id="liste-cartes"),
            # Modale Statut
            dbc.Modal([
                dbc.ModalHeader("Changer le statut"),
                dbc.ModalBody([
                    html.P("ID du dépôt", style={'fontWeight': '500', 'marginBottom': '4px'}),
                    html.Div(id="modal-status-id", style={'fontSize': '18px', 'fontWeight': '700', 'marginBottom': '16px'}),
                    html.P("Nouveau statut", style={'fontWeight': '500', 'marginBottom': '4px'}),
                    dcc.Dropdown(
                        id="modal-status-select",
                        options=[
                            {'label': 'En attente', 'value': 'en_attente'},
                            {'label': 'En cours', 'value': 'en_cours'},
                            {'label': 'Résolu', 'value': 'resolu'}
                        ],
                        value='en_attente'
                    )
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="modal-status-close", className="ms-auto", n_clicks=0),
                    dbc.Button("Confirmer", id="modal-status-confirm", color="primary")
                ])
            ], id="modal-status", is_open=False),
            # Modale Priorité
            dbc.Modal([
                dbc.ModalHeader("Changer la priorité"),
                dbc.ModalBody([
                    html.P("ID du dépôt", style={'fontWeight': '500', 'marginBottom': '4px'}),
                    html.Div(id="modal-priorite-id", style={'fontSize': '18px', 'fontWeight': '700', 'marginBottom': '16px'}),
                    html.P("Nouvelle priorité", style={'fontWeight': '500', 'marginBottom': '4px'}),
                    dcc.Dropdown(
                        id="modal-priorite-select",
                        options=[
                            {'label': 'Urgent', 'value': 'urgent'},
                            {'label': 'Moyen', 'value': 'moyen'},
                            {'label': 'Normal', 'value': 'normal'}
                        ],
                        value='normal'
                    )
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="modal-priorite-close", className="ms-auto", n_clicks=0),
                    dbc.Button("Confirmer", id="modal-priorite-confirm", color="primary")
                ])
            ], id="modal-priorite", is_open=False),
            # Modale Suppression
            dbc.Modal([
                dbc.ModalHeader("Confirmer la suppression"),
                dbc.ModalBody([
                    html.P("Êtes-vous sûr de vouloir supprimer ce dépôt ?", style={'fontWeight': '500'}),
                    html.Div(id="modal-delete-id", style={'fontSize': '18px', 'fontWeight': '700', 'marginBottom': '16px'}),
                    html.P("Cette action est irréversible.", style={'color': '#ef4444', 'fontWeight': '500'})
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="modal-delete-close", className="ms-auto", n_clicks=0),
                    dbc.Button("Supprimer", id="modal-delete-confirm", color="danger")
                ])
            ], id="modal-delete", is_open=False),
            # Modale Photo
            dbc.Modal([
                dbc.ModalHeader("Photo du dépôt"),
                dbc.ModalBody([
                    html.Div(id="modal-photo-container", style={'textAlign': 'center'})
                ]),
                dbc.ModalFooter([
                    dbc.Button("Fermer", id="modal-photo-close", className="ms-auto", n_clicks=0)
                ])
            ], id="modal-photo", is_open=False, size="lg"),
            # Modale Carte
            dbc.Modal([
                dbc.ModalHeader("Localisation du dépôt"),
                dbc.ModalBody([
                    html.Div(id="modal-map-container", style={'width': '100%'})
                ]),
                dbc.ModalFooter([
                    dbc.Button("Fermer", id="modal-map-close", className="ms-auto", n_clicks=0)
                ])
            ], id="modal-map", is_open=False, size="xl")
        ], className="content-card")
    ])

# ==================== PAGE STATISTIQUES ====================
def page_stats():
    return html.Div([
        html.H1("Statistiques", className="page-title"),
        html.P("Analyse complète des données", className="page-subtitle mb-4"),
        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Répartition par priorité", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(id="stats-priorite", config={'displayModeBar': False})
                        ])
                    ], className="shadow-sm border-0")
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Répartition par statut", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(id="stats-statut", config={'displayModeBar': False})
                        ])
                    ], className="shadow-sm border-0")
                ], md=6),
            ], className="mb-4"),
            dbc.Card([
                dbc.CardHeader(html.H5("Top 10 des dépôts par volume", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id="stats-volume", config={'displayModeBar': False})
                ])
            ], className="shadow-sm border-0"),
            dcc.Interval(id="interval-stats-graphs", interval=30000)
        ])
    ])

# ==================== PAGE TESTER ====================
def page_tester():
    return html.Div([
        html.H1("Tester", className="page-title"),
        html.P("Analysez une photo en temps réel", className="page-subtitle mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Téléchargez une photo", className="mb-0")),
                    dbc.CardBody([
                        dcc.Upload(
                            id="upload-photo",
                            children=html.Div([
                                html.I(className="fas fa-cloud-upload-alt", style={'fontSize': '48px', 'color': '#00d4ff'}),
                                html.P("Glissez-déposez ou cliquez pour sélectionner une photo", className="mt-2", style={'color': '#64748b'})
                            ], className="upload-area"),
                            multiple=False
                        ),
                        html.Div(id="upload-status", className="mt-2 text-center"),
                        html.Hr(),
                        html.H5("Position GPS", className="mb-3"),
                        html.Div([
                            html.I(className="fas fa-satellite-dish", style={'color': '#00d4ff'}),
                            html.Span(" Le GPS sera automatiquement détecté depuis la photo", className="text-muted", style={'fontSize': '14px'})
                        ], className="mb-2"),
                        html.Div([
                            html.I(className="fas fa-map-pin", style={'color': '#64748b'}),
                            html.Span(" Si non disponible, utilisez les champs ci-dessous", className="text-muted", style={'fontSize': '13px'})
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Latitude (secours)", style={'fontSize': '13px', 'color': '#64748b'}),
                                dcc.Input(
                                    id="analyse-lat",
                                    type="number",
                                    value=12.6392,
                                    step=0.000001,
                                    className="form-control",
                                    style={'borderRadius': '8px'}
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label("Longitude (secours)", style={'fontSize': '13px', 'color': '#64748b'}),
                                dcc.Input(
                                    id="analyse-lon",
                                    type="number",
                                    value=-8.0029,
                                    step=0.000001,
                                    className="form-control",
                                    style={'borderRadius': '8px'}
                                )
                            ], md=6),
                        ]),
                        html.Div([
                            dbc.Button(
                                html.Div([
                                    html.I(className="fas fa-rocket me-2"),
                                    "Lancer l'analyse"
                                ]),
                                id="btn-analyser",
                                color="primary",
                                className="mt-3 w-100",
                                style={'padding': '12px', 'fontWeight': '600', 'borderRadius': '10px'}
                            )
                        ])
                    ])
                ], className="shadow-sm border-0 rounded-3")
            ], md=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Résultat de l'analyse", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="analyse-result", className="text-center")
                    ])
                ], className="shadow-sm border-0 rounded-3")
            ], md=7),
        ])
    ])

# ==================== CALLBACKS ====================
@app.callback(
    Output("stats-container", "children"),
    Input("interval-stats", "n_intervals")
)
def update_stats_dashboard(n):
    stats = get_stats_dashboard()
    if not stats:
        return html.Div("Impossible de charger les données", className="text-danger")
    return html.Div([
        html.Div([
            create_stat_card("Total", stats.get('total', 0), "blue"),
            create_stat_card("Urgents", stats.get('urgent', 0), "red"),
            create_stat_card("Moyens", stats.get('moyen', 0), "orange"),
            create_stat_card("Normaux", stats.get('normal', 0), "green")
        ], className="stats-grid"),
        html.Div([
            create_stat_card("En attente", stats.get('attente', 0), "orange"),
            create_stat_card("En cours", stats.get('cours', 0), "blue"),
            create_stat_card("Résolus", stats.get('resolu', 0), "green")
        ], className="stats-grid-3"),
        html.Div([
            html.Div([
                html.I(className="fas fa-calendar-day me-2", style={'color': '#64748b'}),
                html.Span(f"Aujourd'hui : {date.today().strftime('%d %B %Y')}", style={'color': '#64748b', 'fontSize': '14px'})
            ], className="text-center py-2")
        ], className="content-card", style={'marginTop': '16px'})
    ])

# ==================== CALLBACK LISTE ====================
@app.callback(
    Output("liste-cartes", "children"),
    [Input("btn-apply-filters", "n_clicks"),
     Input("btn-reset-filters", "n_clicks")],
    [State("filtre-priorite", "value"),
     State("filtre-statut", "value"),
     State("search-id", "value")]
)
def update_liste_cartes(n_apply, n_reset, priorite, statut, search_id):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        priorite = 'tous'
        statut = 'tous'
        search_id = None
    
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('btn-reset-filters'):
        priorite = 'tous'
        statut = 'tous'
        search_id = None
    
    try:
        depots = get_depots_filtres(priorite, statut)
    except Exception as e:
        print(f"❌ Erreur get_depots_filtres : {e}")
        depots = []
    
    if search_id:
        depots = [d for d in depots if d['id'] == search_id]
    
    if not depots:
        return html.Div("Aucun dépôt trouvé", className="text-muted", style={'padding': '40px', 'textAlign': 'center'})
    
    cartes = []
    for d in depots:
        priorite_class = f"badge-{d['priorite']}" if d['priorite'] in ['urgent', 'moyen', 'normal'] else 'badge-normal'
        statut_class = f"badge-{d['statut']}" if d['statut'] in ['en_attente', 'en_cours', 'resolu'] else 'badge-attente'
        
        try:
            adresse = get_address(d['latitude'], d['longitude'])
        except:
            adresse = "Position non disponible"
        
        photo_chemin = d.get('photo_chemin', '')
        photo_existe = os.path.exists(photo_chemin) if photo_chemin else False
        
        cartes.append(html.Div([
            html.Div([
                html.Div([
                    html.Span(f"#{d['id']}", className="depot-id"),
                    html.Span(d['date'], className="depot-date"),
                    html.Span(f"{d['volume']} m³", className="depot-volume"),
                    html.Span(d['priorite'], className=f"badge {priorite_class}"),
                    html.Span(d['statut'], className=f"badge {statut_class}"),
                    html.Span(adresse, className="text-muted", style={'fontSize': '12px'}),
                ], className="depot-info"),
                html.Div([
                    html.Button("Photo", className="action-btn btn-photo",
                               id={'type': 'btn-photo', 'index': d['id']}, n_clicks=0,
                               style={'marginRight': '4px'}),
                    html.Button(
                        "Carte",
                        className="action-btn btn-maps",
                        id={'type': 'btn-maps', 'index': d['id']},
                        n_clicks=0,
                        style={'marginRight': '4px'}
                    ),
                    html.Button("Statut", className="action-btn btn-status", 
                               id={'type': 'btn-status', 'index': d['id']}, n_clicks=0,
                               style={'marginRight': '4px'}),
                    html.Button("Priorité", className="action-btn btn-priorite",
                               id={'type': 'btn-priorite', 'index': d['id']}, n_clicks=0,
                               style={'marginRight': '4px'}),
                    html.Button("Supprimer", className="action-btn btn-delete",
                               id={'type': 'btn-delete', 'index': d['id']}, n_clicks=0),
                ], className="depot-actions")
            ], className="depot-card")
        ]))
    
    return cartes

# ==================== CALLBACKS MODALES ====================
@app.callback(
    Output("modal-status", "is_open"),
    Output("modal-status-id", "children"),
    Input({'type': 'btn-status', 'index': ALL}, 'n_clicks'),
    Input("modal-status-close", "n_clicks"),
    prevent_initial_call=True
)
def open_status_modal(status_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "modal-status-close":
        return False, ""
    
    try:
        btn_data = json.loads(trigger_id)
        depot_id = btn_data.get('index')
        return True, f"#{depot_id}"
    except:
        return False, ""

@app.callback(
    Output("modal-status", "is_open", allow_duplicate=True),
    Input("modal-status-confirm", "n_clicks"),
    State("modal-status-id", "children"),
    State("modal-status-select", "value"),
    prevent_initial_call=True
)
def confirm_status(n, depot_id, statut):
    if n is None or not depot_id:
        return False
    depot_id = int(depot_id.replace('#', ''))
    update_status_db(depot_id, statut)
    return False

@app.callback(
    Output("modal-priorite", "is_open"),
    Output("modal-priorite-id", "children"),
    Input({'type': 'btn-priorite', 'index': ALL}, 'n_clicks'),
    Input("modal-priorite-close", "n_clicks"),
    prevent_initial_call=True
)
def open_priorite_modal(priorite_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "modal-priorite-close":
        return False, ""
    
    try:
        btn_data = json.loads(trigger_id)
        depot_id = btn_data.get('index')
        return True, f"#{depot_id}"
    except:
        return False, ""

@app.callback(
    Output("modal-priorite", "is_open", allow_duplicate=True),
    Input("modal-priorite-confirm", "n_clicks"),
    State("modal-priorite-id", "children"),
    State("modal-priorite-select", "value"),
    prevent_initial_call=True
)
def confirm_priorite(n, depot_id, priorite):
    if n is None or not depot_id:
        return False
    depot_id = int(depot_id.replace('#', ''))
    update_priorite_db(depot_id, priorite)
    return False

@app.callback(
    Output("modal-delete", "is_open"),
    Output("modal-delete-id", "children"),
    Input({'type': 'btn-delete', 'index': ALL}, 'n_clicks'),
    Input("modal-delete-close", "n_clicks"),
    prevent_initial_call=True
)
def open_delete_modal(delete_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "modal-delete-close":
        return False, ""
    
    try:
        btn_data = json.loads(trigger_id)
        depot_id = btn_data.get('index')
        return True, f"#{depot_id}"
    except:
        return False, ""

@app.callback(
    Output("modal-delete", "is_open", allow_duplicate=True),
    Input("modal-delete-confirm", "n_clicks"),
    State("modal-delete-id", "children"),
    prevent_initial_call=True
)
def confirm_delete(n, depot_id):
    if n is None or not depot_id:
        return False
    depot_id = int(depot_id.replace('#', ''))
    delete_depot_db(depot_id)
    return False

# ==================== CALLBACK PHOTO ====================
@app.callback(
    Output("modal-photo", "is_open"),
    Output("modal-photo-container", "children"),
    Input({'type': 'btn-photo', 'index': ALL}, 'n_clicks'),
    Input("modal-photo-close", "n_clicks"),
    prevent_initial_call=True
)
def open_photo_modal(photo_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, html.Div()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "modal-photo-close":
        return False, html.Div()
    
    try:
        btn_data = json.loads(trigger_id)
        depot_id = btn_data.get('index')
        
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT photo_chemin, photo_nom FROM signalements WHERE id = %s", (depot_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                photo_path = result[0]
                photo_nom = result[1] or "Photo"
                
                if os.path.exists(photo_path):
                    with open(photo_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                    src = f"data:image/jpeg;base64,{encoded}"
                    
                    return True, html.Div([
                        html.P(f"{photo_nom}", style={'textAlign': 'center', 'fontWeight': '600', 'marginBottom': '10px'}),
                        html.Img(src=src, style={'width': '100%', 'borderRadius': '8px', 'maxHeight': '600px', 'objectFit': 'contain'})
                    ])
                else:
                    return True, html.Div([
                        html.P("Photo non trouvée sur le serveur", className="text-center text-muted")
                    ])
            else:
                return True, html.Div([
                    html.P("Aucune photo associée à ce dépôt", className="text-center text-muted")
                ])
        return False, html.Div()
    except Exception as e:
        print(f"❌ Erreur photo : {e}")
        return False, html.Div()

# ==================== CALLBACK CARTE ====================
@app.callback(
    Output("modal-map", "is_open"),
    Output("modal-map-container", "children"),
    Input({'type': 'btn-maps', 'index': ALL}, 'n_clicks'),
    Input("modal-map-close", "n_clicks"),
    prevent_initial_call=True
)
def open_maps_modal(maps_clicks, close_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, html.Div()

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "modal-map-close":
        return False, html.Div()

    try:
        btn_data = json.loads(trigger_id)
        depot_id = btn_data.get('index')

        conn = get_connection()
        if not conn:
            return False, html.Div()

        cursor = conn.cursor()
        cursor.execute("""
            SELECT latitude, longitude, volume, priorite, statut
            FROM signalements
            WHERE id = %s
        """, (depot_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return True, html.Div([
                html.P("Dépôt introuvable", className="text-center text-muted")
            ])

        lat = float(result[0])
        lon = float(result[1])
        volume = result[2]
        priorite = result[3]
        statut = result[4]

        if abs(lat - 12.6392) < 0.0001 and abs(lon - (-8.0029)) < 0.0001:
            return True, html.Div([
                html.Div([
                    html.I(
                        className="fas fa-map-marker-alt",
                        style={'fontSize': '45px', 'color': '#94a3b8'}
                    ),
                    html.H5("Position non disponible", className="mt-3"),
                    html.P(f"Dépôt #{depot_id}", className="text-muted"),
                    html.P(
                        "Aucune coordonnée GPS valide n'est associée à ce dépôt.",
                        className="text-muted"
                    )
                ], className="text-center py-5")
            ])

        try:
            adresse = get_address(lat, lon)
        except Exception:
            adresse = "Position non disponible"

        carte_depot = folium.Map(
            location=[lat, lon],
            zoom_start=17,
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='&copy; OpenStreetMap &copy; CartoDB'
        )

        couleurs = {
            'urgent': 'red',
            'moyen': 'orange',
            'normal': 'green'
        }
        couleur = couleurs.get(priorite, 'blue')

        popup_text = f"""
        <div style="font-family: Arial; min-width: 180px;">
            <b>Dépôt #{depot_id}</b><br><br>
            Volume : {volume} m³<br>
            Priorité : {priorite}<br>
            Statut : {statut}<br>
            {adresse}
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Dépôt #{depot_id}",
            icon=folium.Icon(color=couleur, icon='trash', prefix='fa')
        ).add_to(carte_depot)

        folium.Circle(
            location=[lat, lon],
            radius=100,
            color=couleur,
            fill=True,
            fill_opacity=0.15
        ).add_to(carte_depot)

        map_html = carte_depot._repr_html_()

        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

        return True, html.Div([
            html.Div([
                html.H5(
                    f"Dépôt #{depot_id}",
                    style={'fontWeight': '700', 'marginBottom': '5px'}
                ),
                html.P(
                    adresse,
                    className="text-muted",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    f"{lat:.6f}, {lon:.6f}",
                    className="text-muted",
                    style={'fontSize': '13px'}
                ),
                html.P(
                    f"{volume} m³  |  {priorite}  |  {statut}",
                    className="text-muted",
                    style={'fontSize': '13px'}
                )
            ], className="text-center"),
            html.Hr(),
            html.Div(
                html.Iframe(
                    srcDoc=map_html,
                    width="100%",
                    height="550",
                    style={'border': 'none', 'borderRadius': '10px'}
                ),
                style={
                    'width': '100%',
                    'height': '550px',
                    'overflow': 'hidden',
                    'borderRadius': '10px',
                    'border': '1px solid #e9edf2'
                }
            ),
            html.Div([
                html.A(
                    html.Button(
                        "Ouvrir dans Google Maps",
                        className="btn btn-primary",
                        style={'padding': '10px 18px', 'fontWeight': '600'}
                    ),
                    href=maps_link,
                    target="_blank"
                )
            ], className="text-center mt-3")
        ])

    except Exception as e:
        print(f"❌ Erreur carte dépôt : {e}")
        return True, html.Div([
            html.P(
                f"Erreur lors de l'affichage de la carte : {str(e)}",
                className="text-danger text-center"
            )
        ])

# ==================== CALLBACK UPLOAD ====================
@app.callback(
    Output("upload-status", "children"),
    Input("upload-photo", "contents"),
    State("upload-photo", "filename")
)
def handle_upload(contents, filename):
    if contents is None:
        return ""
    return html.Span(f"Fichier chargé : {filename}", style={'color': '#22c55e'})

# ==================== CALLBACK ANALYSE ====================
@app.callback(
    Output("analyse-result", "children"),
    Input("btn-analyser", "n_clicks"),
    [State("upload-photo", "contents"), 
     State("upload-photo", "filename"),
     State("analyse-lat", "value"), 
     State("analyse-lon", "value")]
)
def analyser_callback(n, contents, filename, lat_manuel, lon_manuel):
    if n is None or contents is None:
        return html.Div([
            html.I(className="fas fa-info-circle", style={'fontSize': '48px', 'color': '#94a3b8'}),
            html.P("Téléchargez une photo et lancez l'analyse", className="text-muted mt-3", style={'fontSize': '16px'})
        ], className="py-5")
    
    try:
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        os.makedirs("images_test", exist_ok=True)
        nom = f"analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        chemin = os.path.join("images_test", nom)
        with open(chemin, 'wb') as f:
            f.write(decoded)
        
        gps_data = get_gps_from_exif(chemin)
        gps_precision = get_gps_precision(chemin)
        date_capture = get_capture_date(chemin)
        
        location_metadata = get_location_from_metadata(chemin)
        filename_info = get_gps_from_filename(chemin)
        all_exif_tags = get_all_exif_tags(chemin)
        
        location_coords = None
        if location_metadata:
            location_name = location_metadata.replace('Lieu détecté: ', '').strip()
            if location_name and len(location_name) > 2:
                location_coords = search_coordinates_by_name(location_name)
                print(f"Recherche coordonnées pour '{location_name}': {location_coords}")
        
        if gps_data:
            lat = gps_data['latitude']
            lon = gps_data['longitude']
            gps_detecte = True
            precision = gps_precision if gps_precision else 5.0
            adresse = get_address(lat, lon)
            gps_source = "GPS détecté dans l'image"
        elif location_coords:
            lat = location_coords['latitude']
            lon = location_coords['longitude']
            gps_detecte = False
            precision = None
            adresse = location_coords.get('address', "Position approximative")
            gps_source = "Coordonnées trouvées par recherche du lieu"
        else:
            lat = lat_manuel
            lon = lon_manuel
            gps_detecte = False
            precision = None
            adresse = "Position non disponible"
            gps_source = "Coordonnées manuelles"
        
        resultat = analyser_photo(chemin)
        priorite = resultat['priorite']
        image_src = f"data:image/jpeg;base64,{base64.b64encode(decoded).decode()}"
        
        elements = [
            html.Div([html.Img(src=image_src, style={'width': '100%', 'borderRadius': '8px', 'maxHeight': '300px', 'objectFit': 'cover'})], className="mb-3"),
            html.H5("Résultat de l'analyse", className="text-center mb-3", style={'color': '#0f172a', 'fontWeight': '600'}),
            html.Hr(),
            html.Div([html.H6("Localisation", style={'fontWeight': '600', 'color': '#0f172a'})]),
        ]
        
        if gps_detecte:
            elements.extend([
                html.Div([html.Span("Source: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(gps_source, style={'fontWeight': '600', 'color': '#22c55e'})], className="mb-1"),
                html.Div([html.Span("Latitude: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{lat:.6f}", style={'fontWeight': '600', 'color': '#0f172a'})], className="mb-1"),
                html.Div([html.Span("Longitude: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{lon:.6f}", style={'fontWeight': '600', 'color': '#0f172a'})], className="mb-1"),
                html.Div([html.Span("Précision: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{precision:.1f} mètres", style={'fontWeight': '600', 'color': '#22c55e'})], className="mb-1"),
                html.Div([html.Span("Adresse: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(adresse, style={'fontWeight': '500', 'color': '#0f172a'})], className="mb-2"),
                html.Div([html.I(className="fas fa-check-circle", style={'color': '#22c55e'}), html.Span(" GPS détecté automatiquement", style={'color': '#22c55e', 'fontSize': '13px'})])
            ])
        elif location_coords:
            elements.extend([
                html.Div([html.Span("Source: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(gps_source, style={'fontWeight': '600', 'color': '#3b82f6'})], className="mb-1"),
                html.Div([html.I(className="fas fa-info-circle", style={'color': '#3b82f6'}), html.Span(" Coordonnées trouvées à partir du lieu détecté", style={'color': '#3b82f6', 'fontSize': '13px'})], className="mb-1"),
                html.Div([html.Span("Latitude: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{lat:.6f}", style={'fontWeight': '600', 'color': '#0f172a'})], className="mb-1"),
                html.Div([html.Span("Longitude: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{lon:.6f}", style={'fontWeight': '600', 'color': '#0f172a'})], className="mb-1"),
                html.Div([html.Span("Adresse: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(adresse, style={'fontWeight': '500', 'color': '#0f172a'})], className="mb-2"),
            ])
        else:
            elements.extend([
                html.Div([html.I(className="fas fa-exclamation-circle", style={'color': '#f59e0b'}), html.Span(" GPS non trouvé dans l'image", style={'color': '#f59e0b', 'fontSize': '13px'})], className="mb-1"),
                html.Div([html.Span("Latitude: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{lat:.6f}", style={'fontWeight': '600', 'color': '#0f172a'})], className="mb-1"),
                html.Div([html.Span("Longitude: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{lon:.6f}", style={'fontWeight': '600', 'color': '#0f172a'})], className="mb-1"),
            ])
        
        if location_metadata:
            elements.extend([
                html.Div([
                    html.I(className="fas fa-info-circle", style={'color': '#3b82f6'}),
                    html.Span(f" {location_metadata}", style={'color': '#3b82f6', 'fontSize': '13px'})
                ], className="mb-2")
            ])
        
        if filename_info and not gps_detecte:
            elements.extend([
                html.Div([
                    html.I(className="fas fa-calendar", style={'color': '#3b82f6'}),
                    html.Span(f" {filename_info}", style={'color': '#3b82f6', 'fontSize': '13px'})
                ], className="mb-2")
            ])
        
        elements.append(html.Hr())
        
        if resultat['nb'] == 0:
            elements.extend([
                html.Div([html.Span("Aucun déchet détecté", style={'color': '#ef4444', 'fontWeight': '600'})], className="mb-1"),
                html.Div([html.Span("Confiance: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span("0%", style={'fontWeight': '600', 'color': '#ef4444'})], className="mb-1"),
            ])
        else:
            for i, d in enumerate(resultat['dechets'], 1):
                elements.append(html.Div([
                    html.Span(f"Déchet #{i}: ", style={'color': '#64748b', 'fontSize': '13px'}),
                    html.Span(d['type'], style={'fontWeight': '600', 'color': '#0f172a'})
                ], className="mb-1"))
                elements.append(html.Div([
                    html.Span("   Confiance: ", style={'color': '#64748b', 'fontSize': '12px'}),
                    html.Span(f"{d['confiance']}%", style={'fontWeight': '600', 'color': '#22c55e'})
                ], className="mb-1"))
            
            nb_dechets = resultat['nb']
            if nb_dechets == 1:
                elements.append(html.Div([
                    html.I(className="fas fa-check-circle", style={'color': '#22c55e'}),
                    html.Span(" 1 déchet détecté", style={'color': '#22c55e', 'fontWeight': '600'})
                ], className="mb-1"))
            else:
                elements.append(html.Div([
                    html.I(className="fas fa-check-circle", style={'color': '#22c55e'}),
                    html.Span(f" {nb_dechets} déchets détectés", style={'color': '#22c55e', 'fontWeight': '600'})
                ], className="mb-1"))
        
        elements.append(html.Hr())
        elements.extend([
            html.Div([html.H6("Estimation & Priorité", style={'fontWeight': '600', 'color': '#0f172a'})]),
            html.Div([html.Span("Surface estimée: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(f"{resultat['volume']} m²", style={'fontWeight': '700', 'color': '#3b82f6', 'fontSize': '18px'})], className="mb-1"),
            html.Div([html.Span("Priorité: ", style={'color': '#64748b', 'fontSize': '13px'}), html.Span(priorite.upper(), style={'fontWeight': '700', 'color': '#ef4444' if priorite == 'urgent' else '#f59e0b' if priorite == 'moyen' else '#22c55e'})], className="mb-2"),
        ])
        
        if resultat['nb'] > 0:
            success = add_detection(lat, lon, resultat['volume'], priorite, 'en_attente', nom)
            elements.append(html.Div([
                html.Hr(),
                html.Div([
                    html.I(className="fas fa-save me-1", style={'color': '#22c55e' if success else '#ef4444'}),
                    html.Span("Sauvegardé dans la base" if success else "Erreur sauvegarde", 
                             style={'color': '#22c55e' if success else '#ef4444', 'fontSize': '14px'})
                ])
            ]))
        
        return html.Div(elements, style={'padding': '8px'})
    except Exception as e:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle", style={'fontSize': '32px', 'color': '#ef4444'}),
            html.P(f"Erreur : {str(e)}", className="text-danger mt-2")
        ], className="text-center py-3")

# ==================== CALLBACK STATS GRAPHIQUES ====================
@app.callback(
    [Output("stats-priorite", "figure"),
     Output("stats-statut", "figure"),
     Output("stats-volume", "figure")],
    Input("interval-stats-graphs", "n_intervals")
)
def update_stats_graphs(n):
    def create_empty_figure(message="Aucune donnée disponible"):
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#64748b")
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig
    
    try:
        conn = get_connection()
        if not conn:
            fig_empty = create_empty_figure("Impossible de se connecter à la base de données")
            return fig_empty, fig_empty, fig_empty
        
        try:
            df = pd.read_sql("""
                SELECT 
                    priorite,
                    statut,
                    volume,
                    id
                FROM signalements 
                ORDER BY date_creation DESC
            """, conn)
            conn.close()
        except Exception as e:
            print(f"❌ Erreur lecture SQL: {e}")
            fig_empty = create_empty_figure(f"Erreur de lecture: {str(e)}")
            return fig_empty, fig_empty, fig_empty
        
        if df.empty:
            fig_empty = create_empty_figure("Aucune donnée dans la base")
            return fig_empty, fig_empty, fig_empty
        
        # --- Graphique 1: Priorité ---
        try:
            priorite_counts = df['priorite'].value_counts().reset_index()
            priorite_counts.columns = ['priorite', 'count']
            
            priorite_labels = {'urgent': 'Urgent', 'moyen': 'Moyen', 'normal': 'Normal'}
            priorite_counts['label'] = priorite_counts['priorite'].map(priorite_labels).fillna(priorite_counts['priorite'])
            
            couleurs_priorite = {'urgent': '#ef4444', 'moyen': '#f59e0b', 'normal': '#22c55e'}
            couleurs = [couleurs_priorite.get(p, '#94a3b8') for p in priorite_counts['priorite']]
            
            fig_priorite = go.Figure()
            if not priorite_counts.empty:
                fig_priorite.add_trace(go.Pie(
                    labels=priorite_counts['label'],
                    values=priorite_counts['count'],
                    marker=dict(colors=couleurs),
                    textposition='inside',
                    textinfo='percent+label',
                    hoverinfo='label+value+percent',
                    pull=[0.05 if i == 0 else 0 for i in range(len(priorite_counts))]
                ))
            else:
                fig_priorite.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#94a3b8"))
            
            fig_priorite.update_layout(
                title=dict(text="Répartition par priorité", font=dict(size=16, color="#0f172a")),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#0f172a',
                height=350,
                margin=dict(l=20, r=20, t=50, b=20)
            )
        except Exception as e:
            print(f"❌ Erreur graphique priorité: {e}")
            fig_priorite = create_empty_figure("Erreur graphique priorité")
        
        # --- Graphique 2: Statut ---
        try:
            statut_counts = df['statut'].value_counts().reset_index()
            statut_counts.columns = ['statut', 'count']
            
            statut_labels = {'en_attente': 'En attente', 'en_cours': 'En cours', 'resolu': 'Résolu'}
            statut_counts['label'] = statut_counts['statut'].map(statut_labels).fillna(statut_counts['statut'])
            
            couleurs_statut = {'en_attente': '#f59e0b', 'en_cours': '#3b82f6', 'resolu': '#22c55e'}
            statut_couleurs = [couleurs_statut.get(s, '#94a3b8') for s in statut_counts['statut']]
            
            fig_statut = go.Figure()
            if not statut_counts.empty:
                fig_statut.add_trace(go.Pie(
                    labels=statut_counts['label'],
                    values=statut_counts['count'],
                    marker=dict(colors=statut_couleurs),
                    textposition='inside',
                    textinfo='percent+label',
                    hoverinfo='label+value+percent',
                    pull=[0.05 if i == 0 else 0 for i in range(len(statut_counts))]
                ))
            else:
                fig_statut.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#94a3b8"))
            
            fig_statut.update_layout(
                title=dict(text="Répartition par statut", font=dict(size=16, color="#0f172a")),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#0f172a',
                height=350,
                margin=dict(l=20, r=20, t=50, b=20)
            )
        except Exception as e:
            print(f"❌ Erreur graphique statut: {e}")
            fig_statut = create_empty_figure("Erreur graphique statut")
        
        # --- Graphique 3: Volume ---
        try:
            top_volumes = df.nlargest(10, 'volume')[['id', 'volume']]
            
            fig_volume = go.Figure()
            if not top_volumes.empty:
                fig_volume.add_trace(go.Bar(
                    x=top_volumes['id'].astype(str),
                    y=top_volumes['volume'],
                    marker=dict(
                        color=top_volumes['volume'],
                        colorscale='Blues',
                        showscale=True,
                        colorbar=dict(title="Volume (m³)", tickformat='.2f')
                    ),
                    text=top_volumes['volume'].round(2),
                    textposition='outside',
                    texttemplate='%{text:.2f} m²'
                ))
            else:
                fig_volume.add_annotation(text="Aucune donnée", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#94a3b8"))
            
            fig_volume.update_layout(
                title=dict(text="Top 10 des dépôts par volume", font=dict(size=16, color="#0f172a")),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#0f172a',
                xaxis_title="ID du dépôt",
                yaxis_title="Volume (m³)",
                height=350,
                margin=dict(l=20, r=20, t=50, b=30),
                xaxis=dict(showgrid=True, gridcolor='#e9edf2', showline=True, linecolor='#e9edf2'),
                yaxis=dict(showgrid=True, gridcolor='#e9edf2', showline=True, linecolor='#e9edf2', tickformat='.2f')
            )
        except Exception as e:
            print(f"❌ Erreur graphique volume: {e}")
            fig_volume = create_empty_figure("Erreur graphique volume")
        
        return fig_priorite, fig_statut, fig_volume
        
    except Exception as e:
        print(f"❌ Erreur générale stats graphiques : {e}")
        fig_error = create_empty_figure(f"Erreur: {str(e)}")
        return fig_error, fig_error, fig_error

# ==================== CALLBACK NAVIGATION ====================
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/liste":
        return page_liste()
    elif pathname == "/stats":
        return page_stats()
    elif pathname == "/tester":
        return page_tester()
    else:
        return page_dashboard()

# ------------ Lancement ------------
if __name__ == "__main__":
    print("SANUYA Dashboard")
    print("http://localhost:8050")
    app.run(debug=True, host='0.0.0.0', port=8050)