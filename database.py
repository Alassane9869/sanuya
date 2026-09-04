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


_mysql_initialized = False

def init_mysql_db():
    """Initialise et migre automatiquement les données vers MySQL sur o2switch sans ouvrir phpMyAdmin."""
    global _mysql_initialized
    try:
        import mysql.connector
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Création automatique de la table si inexistante
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `signalements` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `latitude` DOUBLE NOT NULL,
                `longitude` DOUBLE NOT NULL,
                `volume` DOUBLE DEFAULT 0.0,
                `priorite` VARCHAR(50) DEFAULT 'normal',
                `statut` VARCHAR(50) DEFAULT 'en_attente',
                `date_creation` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `photo_nom` VARCHAR(255) NULL,
                `photo_chemin` VARCHAR(500) NULL,
                `dechets_detectes` TEXT NULL,
                `nb_dechets` INT DEFAULT 1,
                `est_doublon` TINYINT(1) DEFAULT 0,
                `doublon_de` INT NULL,
                INDEX `idx_statut` (`statut`),
                INDEX `idx_priorite` (`priorite`),
                INDEX `idx_coords` (`latitude`, `longitude`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        conn.commit()
        
        # 2. Vérifier si des données existent déjà
        cursor.execute("SELECT COUNT(*) FROM `signalements`")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("[O2SWITCH] Base MySQL vide. Démarrage de la migration automatique des données...")
            migre = False
            
            # Source 1 : sanuya.db (données réelles SQLite complètes)
            if os.path.exists(SQLITE_PATH):
                try:
                    s_conn = sqlite3.connect(SQLITE_PATH)
                    s_conn.row_factory = sqlite3.Row
                    s_cur = s_conn.cursor()
                    s_cur.execute("SELECT * FROM signalements")
                    lignes = s_cur.fetchall()
                    for r in lignes:
                        cursor.execute("""
                            INSERT INTO `signalements` 
                            (`id`, `latitude`, `longitude`, `volume`, `priorite`, `statut`, `date_creation`, `photo_nom`, `photo_chemin`, `dechets_detectes`, `nb_dechets`, `est_doublon`, `doublon_de`)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE `statut`=VALUES(`statut`), `priorite`=VALUES(`priorite`), `volume`=VALUES(`volume`)
                        """, (
                            r['id'], r['latitude'], r['longitude'], r['volume'],
                            r['priorite'], r['statut'], r['date_creation'],
                            r['photo_nom'], r['photo_chemin'], r['dechets_detectes'],
                            r['nb_dechets'], r['est_doublon'], r['doublon_de']
                        ))
                    conn.commit()
                    s_conn.close()
                    print(f"[O2SWITCH MIGRATION OK] {len(lignes)} signalements migrés de SQLite vers MySQL !")
                    migre = True
                except Exception as e_sql:
                    print(f"[O2SWITCH MIGRATION WARN] Erreur SQLite -> MySQL : {e_sql}")
            
            # Source 2 : donnees_depots_export.csv (secours si pas de sanuya.db)
            if not migre and os.path.exists(CSV_EXPORT_PATH):
                try:
                    df = pd.read_csv(CSV_EXPORT_PATH)
                    images_dir = os.path.join(BASE_DIR, "images_test")
                    images_dispo = sorted([f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]) if os.path.exists(images_dir) else []
                    
                    for idx, row in df.iterrows():
                        img_name = images_dispo[idx % len(images_dispo)] if images_dispo else None
                        img_path = f"images_test/{img_name}" if img_name else None
                        date_val = str(row.get('date', '')).strip()
                        if len(date_val) == 16:
                            date_val += ":00"
                        cursor.execute("""
                            INSERT INTO `signalements` 
                            (`id`, `latitude`, `longitude`, `volume`, `priorite`, `statut`, `date_creation`, `photo_nom`, `photo_chemin`, `dechets_detectes`, `nb_dechets`)
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
                    print(f"[O2SWITCH MIGRATION OK] {len(df)} signalements importés depuis le CSV vers MySQL !")
                except Exception as e_csv:
                    print(f"[O2SWITCH MIGRATION WARN] Erreur CSV -> MySQL : {e_csv}")
                    
        cursor.close()
        conn.close()
        _mysql_initialized = True
        return True, "Base MySQL vérifiée et synchronisée avec succès !"
    except Exception as e:
        print(f"[O2SWITCH MIGRATION ERREUR] : {e}")
        return False, str(e)


def get_connection():
    """Retourne une connexion à la base de données (SQLite avec CustomConnection ou MySQL si configuré)."""
    global _mysql_initialized
    if DB_BACKEND == 'mysql':
        try:
            import mysql.connector
            if not _mysql_initialized:
                init_mysql_db()
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


def backup_database():
    """Crée une copie de sauvegarde automatique horodatée de la base SQLite."""
    try:
        if not os.path.exists(SQLITE_PATH):
            return None
        import shutil
        backup_dir = os.path.join(BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"sanuya_backup_{timestamp}.db")
        shutil.copy2(SQLITE_PATH, backup_path)
        
        # Conserver les 10 sauvegardes les plus récentes
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')])
        if len(backups) > 10:
            for old in backups[:-10]:
                try:
                    os.remove(old)
                except Exception:
                    pass
        print(f"[OK] Sauvegarde automatique creee : {os.path.basename(backup_path)}")
        return backup_path
    except Exception as e:
        print(f"[ERREUR] Erreur backup database: {e}")
        return None