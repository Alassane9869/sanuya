# passenger_wsgi.py
# Point d'entrée pour Phusion Passenger sur cPanel o2switch (sanuya.danayaplus.com)

import sys
import os

# Définir le répertoire de travail
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Forcer l'environnement de production
os.environ['SANUYA_DB_BACKEND'] = 'mysql'
os.environ['SANUYA_DB_HOST'] = 'localhost'
os.environ['SANUYA_DB_USER'] = 'vuxe8870_sanuya_bko'
os.environ['SANUYA_DB_PASSWORD'] = '%ri-l5ac8J?ahGGN'
os.environ['SANUYA_DB_NAME'] = 'vuxe8870_sanuya'

# Migration et initialisation automatique de la base MySQL (sans phpMyAdmin)
try:
    from database import init_mysql_db
    ok, msg = init_mysql_db()
    print(f"[O2SWITCH STARTUP] {msg}")
except Exception as e:
    print(f"[O2SWITCH STARTUP WARN] {e}")

# Importer l'instance Flask sous-jacente de Dash
from dashboard import server as application

