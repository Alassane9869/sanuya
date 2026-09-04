#!/bin/bash
# ============================================================
# SANUYA - Lancement du déploiement & migration en 1 clic
# ============================================================

echo "🚀 Démarrage du déploiement SANUYA sur o2switch..."

# Détection de Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python n'a pas été trouvé."
    exit 1
fi

# Exécution du script de déploiement et migration complet
$PYTHON_CMD deploy_o2switch.py
