# config.py
# Configuration Base de données SANUYA

# Type de base de données : 'sqlite' (recommandé et autonome) ou 'mysql'
DB_BACKEND = 'sqlite'
SQLITE_DB = 'sanuya.db'

# Configuration MySQL (utilisée si DB_BACKEND = 'mysql')
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '27142005',  
    'database': 'sanuya'
}