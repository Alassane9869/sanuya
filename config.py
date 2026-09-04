# config.py
# Configuration Base de données SANUYA (Production o2switch & Développement local)
import os

# Détection automatique de l'environnement de production o2switch
IS_O2SWITCH = os.path.exists('/home/vuxe8870')

# Type de base de données : 'mysql' en production o2switch, 'sqlite' en local
DB_BACKEND = os.getenv('SANUYA_DB_BACKEND', 'mysql' if IS_O2SWITCH else 'sqlite')
SQLITE_DB = 'sanuya.db'

# Configuration MySQL Production o2switch (sanuya.danayaplus.com)
DB_CONFIG = {
    'host': os.getenv('SANUYA_DB_HOST', 'localhost'),
    'user': os.getenv('SANUYA_DB_USER', 'vuxe8870_sanuya_bko'),
    'password': os.getenv('SANUYA_DB_PASSWORD', '%ri-l5ac8J?ahGGN'),
    'database': os.getenv('SANUYA_DB_NAME', 'vuxe8870_sanuya'),
    'port': int(os.getenv('SANUYA_DB_PORT', 3306)),
    'charset': 'utf8mb4'
}

DOMAINE_PRODUCTION = "sanuya.danayaplus.com"