# database.py
# Connexion à MySQL

import mysql.connector
import pandas as pd
from config import DB_CONFIG

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Erreur MySQL : {e}")
        return None

def get_signalements():
    """Récupère tous les signalements"""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    
    query = """
    SELECT id, date_creation, latitude, longitude, 
           photo_nom, dechets_detectes, nb_dechets, 
           statut, est_doublon, doublon_de
    FROM signalements
    ORDER BY date_creation DESC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df