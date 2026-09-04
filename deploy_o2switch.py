#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SANUYA - Script de Déploiement Complet & Migration Automatique pour o2switch
=============================================================================
Ce script réalise 100% de la mise en production en UNE SEULE COMMANDE :
1. Installation automatique de toutes les dépendances pip (requirements.txt)
2. Connexion à la base MySQL o2switch (vuxe8870_sanuya)
3. Création automatique des tables (AUCUN BESOIN D'OUVRIR PHPMYADMIN)
4. Migration intégrale des signalements réels de Bamako vers MySQL
5. Redémarrage automatique du serveur Passenger (sanuya.danayaplus.com)
=============================================================================
"""

import sys
import os
import subprocess
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Identifiants o2switch
DB_HOST = os.getenv('SANUYA_DB_HOST', 'localhost')
DB_USER = os.getenv('SANUYA_DB_USER', 'vuxe8870_sanuya_bko')
DB_PASS = os.getenv('SANUYA_DB_PASSWORD', '%ri-l5ac8J?ahGGN')
DB_NAME = os.getenv('SANUYA_DB_NAME', 'vuxe8870_sanuya')
SQLITE_FILE = os.path.join(BASE_DIR, 'sanuya.db')
CSV_FILE = os.path.join(BASE_DIR, 'donnees_depots_export.csv')
REQ_FILE = os.path.join(BASE_DIR, 'requirements.txt')

def print_step(num, title):
    print("\n" + "="*65)
    print(f"[{num}/4] 🚀 {title}")
    print("="*65)

def etape_1_installer_dependances():
    print_step(1, "INSTALLATION DES DÉPENDANCES PIP")
    if not os.path.exists(REQ_FILE):
        print("❌ Fichier requirements.txt introuvable !")
        return False
    
    print(f"📦 Interpréteur Python actif : {sys.executable}")
    print("⏳ Installation des bibliothèques nécessaires (Dash, OpenCV headless, YOLO, MySQL, etc.)...")
    
    cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", REQ_FILE]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("✅ Toutes les dépendances sont installées avec succès !")
        return True
    else:
        print("⚠️ Erreur lors de l'installation pip. Tentative avec --user...")
        cmd_user = [sys.executable, "-m", "pip", "install", "--user", "-r", REQ_FILE]
        res_user = subprocess.run(cmd_user)
        return res_user.returncode == 0

def etape_2_creer_tables_mysql():
    print_step(2, "CRÉATION DE LA STRUCTURE MYSQL (SANS PHPMYADMIN)")
    try:
        import mysql.connector
    except ImportError:
        print("❌ mysql-connector-python n'est pas encore chargé. Installation d'urgence...")
        subprocess.run([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
        import mysql.connector

    print(f"🔌 Connexion à MySQL sur {DB_HOST} (Base: {DB_NAME}, Utilisateur: {DB_USER})...")
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    table_sql = """
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
    """
    cursor.execute(table_sql)
    conn.commit()
    print("✅ Table `signalements` et index créés avec succès dans MySQL !")
    cursor.close()
    conn.close()
    return True

def etape_3_migrer_donnees():
    print_step(3, "MIGRATION AUTOMATIQUE DES DONNÉES RÉELLES")
    import mysql.connector
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM `signalements`")
    nb_existants = cursor.fetchone()[0]
    
    if nb_existants > 0:
        print(f"ℹ️ La base MySQL contient déjà {nb_existants} signalements enregistrés.")
        print("   Mise à jour et synchronisation en mode sécurisé...")
    else:
        print("📥 Base MySQL vide. Importation complète des signalements...")

    nb_migres = 0
    # Source A : sanuya.db
    if os.path.exists(SQLITE_FILE):
        try:
            s_conn = sqlite3.connect(SQLITE_FILE)
            s_conn.row_factory = sqlite3.Row
            s_cur = s_conn.cursor()
            s_cur.execute("SELECT * FROM signalements")
            rows = s_cur.fetchall()
            for r in rows:
                cursor.execute("""
                    INSERT INTO `signalements` 
                    (`id`, `latitude`, `longitude`, `volume`, `priorite`, `statut`, `date_creation`, `photo_nom`, `photo_chemin`, `dechets_detectes`, `nb_dechets`, `est_doublon`, `doublon_de`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        `volume` = VALUES(`volume`),
                        `priorite` = VALUES(`priorite`),
                        `statut` = VALUES(`statut`),
                        `latitude` = VALUES(`latitude`),
                        `longitude` = VALUES(`longitude`);
                """, (
                    r['id'], r['latitude'], r['longitude'], r['volume'],
                    r['priorite'], r['statut'], r['date_creation'],
                    r['photo_nom'], r['photo_chemin'], r['dechets_detectes'],
                    r['nb_dechets'], r['est_doublon'], r['doublon_de']
                ))
                nb_migres += 1
            conn.commit()
            s_conn.close()
            print(f"✅ {nb_migres} signalements synchronisés depuis sanuya.db !")
        except Exception as e:
            print(f"⚠️ Erreur lecture SQLite : {e}")

    # Contrôle final
    cursor.execute("SELECT COUNT(*) FROM `signalements`")
    total_final = cursor.fetchone()[0]
    print(f"📊 Total des dépôts en base MySQL opérationnelle : {total_final}")
    cursor.close()
    conn.close()
    return True

def etape_4_redemarrer_passenger():
    print_step(4, "REDÉMARRAGE AUTOMATIQUE DU SERVEUR O2SWITCH")
    tmp_dir = os.path.join(BASE_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    restart_file = os.path.join(tmp_dir, "restart.txt")
    with open(restart_file, "w") as f:
        f.write("restart")
    print("✅ Fichier tmp/restart.txt mis à jour (Passenger recharge automatiquement l'application).")
    print("\n" + "*"*65)
    print("🎉 DÉPLOIEMENT & MIGRATION TERMINÉS AVEC SUCCÈS !")
    print("🌐 Votre plateforme est disponible sur :")
    print("   👉 https://sanuya.danayaplus.com")
    print("*"*65 + "\n")

if __name__ == "__main__":
    try:
        ok1 = etape_1_installer_dependances()
        ok2 = etape_2_creer_tables_mysql()
        ok3 = etape_3_migrer_donnees()
        etape_4_redemarrer_passenger()
    except Exception as e:
        print(f"\n❌ ERREUR FATALE : {e}")
        sys.exit(1)
