# database.py
# Module de gestion de base de données pour SANUYA (Support SQLite & MySQL)

import os
import re
import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_CONFIG, DB_BACKEND, SQLITE_DB

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, SQLITE_DB)
CSV_EXPORT_PATH = os.path.join(BASE_DIR, "donnees_depots_export.csv")


class CustomCursor(sqlite3.Cursor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dictionary = False

    def execute(self, sql, params=None):
        sql = sql.replace('%s', '?')
        sql = re.sub(
            r"DATE_FORMAT\s*\(\s*(\w+)\s*,\s*['\"][^'\"]*['\"]\s*\)",
            r"strftime('%d/%m/%Y %H:%M', \1)",
            sql,
            flags=re.IGNORECASE
        )
        sql = re.sub(r"NOW\s*\(\s*\)", "datetime('now', 'localtime')", sql, flags=re.IGNORECASE)
        if params is not None:
            return super().execute(sql, params)
        return super().execute(sql)

    def fetchone(self):
        row = super().fetchone()
        if row is None:
            return None
        if self.dictionary:
            return dict(row)
        return row

    def fetchall(self):
        rows = super().fetchall()
        if self.dictionary:
            return [dict(r) for r in rows]
        return rows


class CustomConnection(sqlite3.Connection):
    def cursor(self, dictionary=False):
        cur = super().cursor(factory=CustomCursor)
        cur.dictionary = dictionary
        return cur


def init_sqlite_db():
    """Initialise la base SQLite si nécessaire et importe les données initiales."""
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, factory=CustomConnection)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signalements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            volume REAL,
            priorite TEXT,
            statut TEXT,
            date_creation TEXT,
            photo_nom TEXT,
            photo_chemin TEXT,
            dechets_detectes TEXT,
            nb_dechets INTEGER,
            est_doublon INTEGER DEFAULT 0,
            doublon_de INTEGER
        )
    """)
    conn.commit()

    # Vérifier si la table contient des données
    cursor.execute("SELECT COUNT(*) FROM signalements")
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(CSV_EXPORT_PATH):
        try:
            df = pd.read_csv(CSV_EXPORT_PATH)
            images_dir = os.path.join(BASE_DIR, "images_test")
            images_dispo = sorted([f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]) if os.path.exists(images_dir) else []
            
            for idx, row in df.iterrows():
                img_name = images_dispo[idx % len(images_dispo)] if images_dispo else None
                img_path = f"images_test/{img_name}" if img_name else None
                date_val = str(row.get('date', '')).strip()
                if len(date_val) == 16:  # '2026-08-11 10:00'
                    date_val += ":00"
                
                cursor.execute("""
                    INSERT INTO signalements 
                    (id, latitude, longitude, volume, priorite, statut, date_creation, photo_nom, photo_chemin, dechets_detectes, nb_dechets)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    int(row['id']) if 'id' in row and pd.notna(row['id']) else None,
                    float(row['latitude']),
                    float(row['longitude']),
                    float(row['volume']) if 'volume' in row and pd.notna(row['volume']) else 0.0,
                    str(row.get('priorite', 'normal')),
                    str(row.get('statut', 'en_attente')),
                    date_val or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    img_name,
                    img_path,
                    "Dechets plastiques, depots divers",
                    1
                ))
            conn.commit()
            print(f"[OK] SQLite initialise avec {len(df)} signalements depuis {CSV_EXPORT_PATH}")
        except Exception as e:
            print(f"[WARNING] Erreur import CSV initial : {e}")

    conn.close()


def get_connection():
    """Retourne une connexion à la base de données (SQLite avec CustomConnection ou MySQL si configuré)."""
    if DB_BACKEND == 'mysql':
        try:
            import mysql.connector
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"[INFO] MySQL indisponible ({e}), bascule automatique sur SQLite.")

    # SQLite
    if not os.path.exists(SQLITE_PATH):
        init_sqlite_db()
    conn = sqlite3.connect(SQLITE_PATH, factory=CustomConnection)
    conn.row_factory = sqlite3.Row
    return conn


def get_signalements():
    """Récupère tous les signalements."""
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