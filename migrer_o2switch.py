#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration et vérification automatique de la base MySQL o2switch.
Exécute la création des tables et le transfert complet des données sans ouvrir phpMyAdmin.
"""

import os
import sys

# Positionner le répertoire de travail
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Forcer la configuration MySQL o2switch
os.environ['SANUYA_DB_BACKEND'] = 'mysql'
os.environ['SANUYA_DB_HOST'] = 'localhost'
os.environ['SANUYA_DB_USER'] = 'vuxe8870_sanuya_bko'
os.environ['SANUYA_DB_PASSWORD'] = '%ri-l5ac8J?ahGGN'
os.environ['SANUYA_DB_NAME'] = 'vuxe8870_sanuya'

from config import DB_CONFIG
from database import init_mysql_db, get_connection

def main():
    print("="*60)
    print("🚀 SANUYA - MIGRATION AUTOMATIQUE MYSQL O2SWITCH")
    print(f"Base cible : {DB_CONFIG['database']} sur {DB_CONFIG['host']}")
    print(f"Utilisateur : {DB_CONFIG['user']}")
    print("="*60)
    
    print("\n⏳ 1. Vérification et initialisation de la base...")
    succes, message = init_mysql_db()
    
    if succes:
        print(f"✅ Succès : {message}")
        
        # Contrôle final
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM signalements")
            total = cursor.fetchone()[0]
            print(f"📊 Nombre total de signalements actifs en base MySQL : {total}")
            
            cursor.execute("SELECT id, priorite, statut, volume, date_creation FROM signalements LIMIT 5")
            print("\n📋 Aperçu des 5 premiers signalements :")
            for r in cursor.fetchall():
                print(f"   • Dépôt #{r[0]} | Priorité: {r[1]} | Statut: {r[2]} | Volume: {r[3]} m³ | Date: {r[4]}")
                
            cursor.close()
            conn.close()
            print("\n🎉 Tout est prêt ! Vous pouvez ouvrir https://sanuya.danayaplus.com")
        except Exception as e:
            print(f"⚠️ Note vérification : {e}")
    else:
        print(f"❌ Erreur lors de l'initialisation : {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
