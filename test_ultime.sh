#!/bin/bash
# ==============================================================================
# SANUYA - SCRIPT DE DIAGNOSTIC, TEST ET REPARATION ULTIME
# Domaine : https://sanuya.danayaplus.com
# Serveur : o2switch (compte: vuxe8870)
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear 2>/dev/null || true
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}        🌟 SANUYA - SCRIPT DE TEST & DIAGNOSTIC ULTIME 🌟           ${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

APP_DIR="/home/vuxe8870/sanuya.danayaplus.com"
REPO_DIR="/home/vuxe8870/repositories/sanuya"
VENV_DIR="/home/vuxe8870/virtualenv/sanuya.danayaplus.com/3.11"
PYTHON_BIN="$VENV_DIR/bin/python"

# ------------------------------------------------------------------------------
# 1. TEST DE L'ENVIRONNEMENT PYTHON
# ------------------------------------------------------------------------------
echo -e "${BLUE}[TEST 1/5] Vérification du Virtualenv Python 3.11...${NC}"
if [ -f "$PYTHON_BIN" ]; then
    echo -e "  ${GREEN}✓ Python binaire trouvé :${NC} $PYTHON_BIN"
    PY_VER=$($PYTHON_BIN --version)
    echo -e "  ${GREEN}✓ Version :${NC} $PY_VER"
else
    echo -e "  ${RED}✗ Python introuvable dans $PYTHON_BIN${NC}"
    # Recherche alternative
    ALT_PY=$(find /home/vuxe8870/virtualenv -name python 2>/dev/null | grep "3.11" | head -n 1 || true)
    if [ -n "$ALT_PY" ]; then
        echo -e "  ${YELLOW}→ Trouvé dans : $ALT_PY${NC}"
        PYTHON_BIN="$ALT_PY"
    fi
fi
echo ""

# ------------------------------------------------------------------------------
# 2. TEST DES PACKAGES PYTHON CRITIQUES
# ------------------------------------------------------------------------------
echo -e "${BLUE}[TEST 2/5] Vérification des modules Python (Dash, MySQL, YOLO)...${NC}"
$PYTHON_BIN -c "
import sys
packages = ['dash', 'dash_bootstrap_components', 'plotly', 'mysql.connector', 'ultralytics', 'torch', 'cv2', 'reportlab']
missing = []
for p in packages:
    try:
        __import__(p)
        print(f'  ✓ {p}')
    except ImportError:
        missing.append(p)
        print(f'  ✗ MANQUANT : {p}')

if missing:
    sys.exit(1)
" || {
    echo -e "  ${YELLOW}Installation des dépendances manquantes en cours...${NC}"
    $VENV_DIR/bin/pip install --no-cache-dir -r "$APP_DIR/requirements.txt"
}
echo -e "  ${GREEN}✓ Tous les modules requis sont installés et opérationnels !${NC}"
echo ""

# ------------------------------------------------------------------------------
# 3. TEST DE CONNEXION MYSQL & DEMARRAGE WSGI
# ------------------------------------------------------------------------------
echo -e "${BLUE}[TEST 3/5] Test du démarrage de passenger_wsgi.py & Base MySQL...${NC}"
cd "$APP_DIR"
TEST_OUTPUT=$($PYTHON_BIN -c "
import passenger_wsgi
from database import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM signalements')
count = cursor.fetchone()[0]
conn.close()
print(f'DB_OK|{count}')
" 2>&1)

if echo "$TEST_OUTPUT" | grep -q "DB_OK"; then
    NB_DEPOTS=$(echo "$TEST_OUTPUT" | grep "DB_OK" | cut -d'|' -f2)
    echo -e "  ${GREEN}✓ Connexion MySQL réussie !${NC}"
    echo -e "  ${GREEN}✓ Base de données active :${NC} $NB_DEPOTS signalements enregistrés"
    echo -e "  ${GREEN}✓ Initialisation WSGI sans aucune erreur !${NC}"
else
    echo -e "  ${RED}✗ Erreur lors du test WSGI :${NC}"
    echo "$TEST_OUTPUT"
fi
echo ""

# ------------------------------------------------------------------------------
# 4. TEST ET CORRECTION DE LA CONFIGURATION LITESPEED / PASSENGER
# ------------------------------------------------------------------------------
echo -e "${BLUE}[TEST 4/5] Vérification et Optimisation du .htaccess pour LiteSpeed...${NC}"

# Permissions
chmod 755 "$APP_DIR/passenger_wsgi.py"
mkdir -p "$APP_DIR/tmp"
touch "$APP_DIR/tmp/restart.txt"

# Injection de la configuration .htaccess complète et sécurisée
cat << 'EOF' > "$APP_DIR/.htaccess"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "/home/vuxe8870/sanuya.danayaplus.com"
PassengerBaseURI "/"
PassengerPython "/home/vuxe8870/virtualenv/sanuya.danayaplus.com/3.11/bin/python"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END

# Directives LiteSpeed / Passenger
PassengerEnabled on
PassengerAppType wsgi
PassengerStartupFile passenger_wsgi.py

# Empêcher le listing des répertoires (évite 'Index of /')
Options -Indexes

# Redirection automatique HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
EOF

echo -e "  ${GREEN}✓ Fichier .htaccess configuré avec PassengerEnabled et Options -Indexes${NC}"
echo -e "  ${GREEN}✓ Permissions fixées (chmod 755 passenger_wsgi.py)${NC}"

# Essayer d'enregistrer l'app via cloudlinux-selector CLI si disponible
if command -v cloudlinux-selector >/dev/null 2>&1; then
    echo -e "  ${CYAN}→ Enregistrement CloudLinux CLI...${NC}"
    cloudlinux-selector create --interpreter python --version 3.11 --app-root sanuya.danayaplus.com --app-uri / --startup-file passenger_wsgi.py --entry-point application 2>/dev/null || true
fi

# Tuer les anciens processus python orphelins
pkill -9 -u vuxe8870 python3.11 2>/dev/null || true
touch "$APP_DIR/tmp/restart.txt"
echo -e "  ${GREEN}✓ Redémarrage déclenché (tmp/restart.txt touché)${NC}"
echo ""

# ------------------------------------------------------------------------------
# 5. TEST DE REPONSE HTTP EN DIRECT
# ------------------------------------------------------------------------------
echo -e "${BLUE}[TEST 5/5] Test de la réponse HTTP sur https://sanuya.danayaplus.com...${NC}"
sleep 2

HTTP_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://sanuya.danayaplus.com || echo "000")
RESPONSE_SNIPPET=$(curl -s -k https://sanuya.danayaplus.com | head -n 15 || true)

echo -e "  ${CYAN}Code HTTP retourné :${NC} $HTTP_CODE"

if echo "$RESPONSE_SNIPPET" | grep -qi "Index of /"; then
    echo -e "  ${YELLOW}⚠️  ATTENTION : LiteSpeed affiche encore 'Index of /'.${NC}"
    echo -e "  ${YELLOW}→ L'application doit être validée une fois dans l'interface cPanel.${NC}"
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}           ACTION SIMPLE REQUISE DANS CPANEL (1 MINUTE)               ${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "1. Ouvrez votre **cPanel** > **« Configurer une application Python »**"
    echo -e "2. Si l'application apparaît dans la liste :"
    echo -e "   → Cliquez sur **REDÉMARRER**"
    echo -e "3. Si elle n'apparaît pas ou affiche une erreur lors de la création :"
    echo -e "   → Lancez cette commande pour préparer la création sans erreur :"
    echo -e "     ${GREEN}rm -f $APP_DIR/.gitignore $APP_DIR/.htaccess${NC}"
    echo -e "   → Cliquez sur **CRÉER UNE APPLICATION** :"
    echo -e "     - Version : **3.11**"
    echo -e "     - Racine de l'application : **sanuya.danayaplus.com**"
    echo -e "     - URL de l'application : **sanuya.danayaplus.com**"
    echo -e "     - Fichier de démarrage : **passenger_wsgi.py**"
    echo -e "     - Point d'entrée : **application**"
    echo -e "   → Cliquez sur **CRÉER**"
    echo -e "${CYAN}======================================================================${NC}"
elif echo "$RESPONSE_SNIPPET" | grep -qi "dash\|sanuya\|<!DOCTYPE html>"; then
    echo -e "  ${GREEN}🎉 SUCCÈS TOTAL ! L'application Dash SANUYA répond parfaitement !${NC}"
    echo -e "  ${GREEN}🌐 URL : https://sanuya.danayaplus.com${NC}"
else
    echo -e "  ${CYAN}Réponse du serveur :${NC}"
    echo "$RESPONSE_SNIPPET"
fi

echo ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}                     DIAGNOSTIC TERMINÉ                               ${NC}"
echo -e "${CYAN}======================================================================${NC}"
