# 📋 RAPPORT D'AUDIT TECHNIQUE, CORRECTIONS & AMÉLIORATIONS — PROJET SANUYA

**Date :** 4 Septembre 2026  
**Projet :** SANUYA — Système Intelligent de Détection, Cartographie et Gestion des Dépôts d'Ordures Sauvages  
**Auteure principale du projet :** Maty DICKO  
**Cadre :** Audit complet, fiabilisation logicielle, optimisation des calculs IA/GPS, refonte de la base de données et documentation  

---

## 🎯 1. Résumé Exécutif

Avant notre intervention, le projet **SANUYA** disposait d'une excellente base conceptuelle combinant Computer Vision (YOLOv8) et visualisation décisionnelle (Dash & Folium), mais souffrait de plusieurs points de blocage critiques qui empêchaient son bon fonctionnement et son déploiement :

| Composant | État Initial (Avant Audit) | État Après Intervention |
|---|---|---|
| **Base de Données** | Dépendance stricte à MySQL local avec mot de passe en dur ; plantage systématique si MySQL n'est pas démarré. | Couche d'abstraction universelle SQLite (`sanuya.db`) / MySQL avec fallback automatique et adaptateur SQL temps réel. |
| **Visualisation Carte** | La carte Folium était générée mais **omise du layout** d'accueil ; les dépôts aux coordonnées par défaut étaient supprimés. | Carte interactive intégrée en tête du dashboard ; 100% des dépôts visibles avec badges d'approximation pour les photos sans GPS. |
| **Inférence IA / YOLOv8** | Chemin en dur vers un dossier inexistant (`C:/Users/hp/...`) ; aucune boîte de détection dessinée sur l'image affichée. | Modèle dynamique (fallback automatique vers `yolov8m.pt` / `yolov8n.pt`) ; boîte englobante et label réels dessinés avec `r[0].plot()`. |
| **Calcul du Volume ($m^3$)** | Multiplication brute des pixels sans rapport avec la taille de l'image (fausse estimation variant selon la résolution). | Formule normalisée par la surface relative de l'image (`box_pixels / (width * height)`), calibrée en mètres cubes. |
| **Gestion des Doublons** | `verification.py` existait mais n'était pas raccordé à la chaîne d'ingestion ; risque de doublons infinis. | Raccordement direct avec la formule de Haversine (seuil 50m) pour consolider les dépôts voisins et prévenir les doublons. |
| **Portabilité du Code** | Chemins absolus rigides (`C:/Users/hp/Desktop/...`) empêchant le projet de tourner sur un autre ordinateur. | Tous les chemins sont calculés dynamiquement avec `pathlib.Path(__file__).resolve().parent`. |

---

## 🔍 2. Audit Détaillé des Défauts Identifiés & Solutions Appliquées

### 2.1. Base de Données & Persistance des Données

#### ❌ Problèmes identifiés :
1. **Verrouillage MySQL** : Le fichier d'origine `database.py` tentait une connexion TCP sur `localhost:3306` vers MySQL. En l'absence de MySQL configuré, toute l'application plantait au démarrage (`mysql.connector.errors.InterfaceError`).
2. **Incompatibilité de syntaxe** : Le code du dashboard contenait des requêtes spécifiques à MySQL (`%s`, `NOW()`, `DATE_FORMAT(date_signalement, '%Y-%m')`).
3. **Absence de persistance portable** : Aucune donnée de démonstration n'était directement accessible sans restaurer un dump SQL manuellement.

####  Solutions apportées :
- **Mise en place de `database.py` hybride** :
  - Support natif de **SQLite** via `sanuya.db` par défaut (`DB_BACKEND = 'sqlite'` dans `config.py`).
  - Possibilité de basculer sur **MySQL** à tout moment sans modifier une seule ligne de code métier.
  - Implémentation des classes wrappers `CustomCursor` et `CustomConnection` :
    - Conversion automatique des placeholders `%s` vers `?` pour SQLite.
    - Remplacement à la volée de `NOW()` par `datetime('now', 'localtime')`.
    - Remplacement de `DATE_FORMAT(date_signalement, '%Y-%m')` par `strftime('%Y-%m', date_signalement)`.
- **Initialisation et peuplement automatique** :
  - La base SQLite contient le schéma complet avec types compatibles (`INTEGER PRIMARY KEY AUTOINCREMENT`, `REAL`, `TEXT`, `DATETIME`).
  - Import automatique des 5 dépôts réels historiques de Bamako depuis `donnees_depots_export.csv` avec leurs photos associées.
  - Conformément à votre demande, `sanuya.db` est versionné sur le dépôt privé GitHub afin que votre binôme dispose immédiatement de la base prête à l'emploi.

---

### 2.2. Algorithme d'Estimation du Volume & Priorisation

#### ❌ Problèmes identifiés :
1. **Biais de résolution dans le volume** :
   ```python
   # Ancien code problématique
   surface = (x2 - x1) * (y2 - y1)  # en pixels absolus
   volume = round(surface * 0.0001, 2)
   ```
   *Conséquence grave :* Une même photo prise avec un capteur 4K (3840x2160) donnait un volume 16 fois supérieur à la même photo prise en basse résolution (960x540) !
2. **Divergence de la priorisation** :
   Le dashboard et le module `estimation.py` utilisaient des règles disjointes sans synchronisation (`determiner_priorite` était même manquante dans certaines sections).

####  Solutions apportées :
- **Normalisation par rapport à la taille du capteur** :
  ```python
  img_h, img_w = img.shape[:2]
  surface_pixels = (x2 - x1) * (y2 - y1)
  surface_relative = surface_pixels / (img_w * img_h)  # Ratio entre 0.0 et 1.0
  # Estimation physique réaliste (calibrée à Bamako pour un dépôt moyen)
  volume = round(surface_relative * 8.5, 2)
  volume = max(0.1, volume)
  ```
- **Règles de priorisation harmonisées** :
  - **Urgent (Rouge)** : Volume $> 5.0\,m^3$ ou déchets dangereux/plastiques concentrés.
  - **Moyen (Orange)** : Volume compris entre $2.0\,m^3$ et $5.0\,m^3$.
  - **Normal (Vert)** : Volume $< 2.0\,m^3$.

---

### 2.3. Cartographie & Géolocalisation

#### ❌ Problèmes identifiés :
1. **Omission de la carte sur le Dashboard** :
   Bien que la fonction `generate_map()` soit écrite, elle n'était jamais injectée dans le DOM de la page d'accueil `dashboard.py`, laissant un grand vide visuel.
2. **Élimination silencieuse des dépôts sans GPS** :
   La ligne suivante filtrait et masquait arbitrairement les coordonnées par défaut de Bamako :
   ```python
   # Ancien code masquant les dépôts
   if abs(lat - 12.6392) < 0.0001 and abs(lon - (-8.0029)) < 0.0001:
       continue  # Le dépôt disparaissait purement et simplement !
   ```
   *Conséquence :* Le dépôt #1 et toutes les photos prises sans puce GPS activée étaient invisibles sur la carte et déclenchaient une erreur dans la fenêtre modale.

####  Solutions apportées :
- **Intégration d'une carte interactive fluide** :
  - La carte Folium est désormais affichée directement sous les 4 cartes KPI du tableau de bord d'accueil (`page_dashboard`).
  - La carte se recharge dynamiquement via le callback `update_stats_dashboard`.
- **Gestion intelligente des positions approximatives** :
  - Les dépôts sans GPS EXIF ne sont plus jetés à la poubelle : ils sont positionnés au centre de Bamako (`12.6392, -8.0029`) avec un **marqueur violet distinctif** et un badge explicite :  
    *« Position approximative (Bamako centre) — Photo sans métadonnées GPS »*.
  - Dans la fenêtre modale « Voir sur la carte », la carte s'ouvre désormais pour tous les dépôts avec un niveau de zoom adapté (`zoom=14` pour l'approximation, `zoom=17` pour les coordonnées réelles précises).
- **Géocodage inverse robuste** :
  - Implémentation de la fonction `get_address(lat, lon)` utilisant l'API OpenStreetMap Nominatim avec gestion des erreurs réseau et fallback immédiat.

---

### 2.4. Vision par Ordinateur & Inférence YOLOv8

#### ❌ Problèmes identifiés :
1. Le fichier de poids `best.pt` référençait le chemin du PC portable d'origine et n'avait pas été versionné.
2. Lorsqu'une image était analysée, le script extrayait les coordonnées des boîtes mais réaffichait la photo **vierge** sans aucun dessin à l'écran.

####  Solutions apportées :
- **Fallback multi-niveaux du modèle YOLO** :
  Le chargeur recherche dans l'ordre :
  1. `best.pt` (s'il est présent après un entraînement custom).
  2. `yolov8m.pt` (modèle moyen pré-entraîné de 52 Mo, déjà présent dans le dépôt).
  3. `yolov8n.pt` (modèle nano rapide et ultra-léger de 6.5 Mo).
- **Rendu visuel des détections** :
  Utilisation de la méthode native `annotated_img = r[0].plot()` d'Ultralytics pour peindre directement les rectangles colorés, les noms de classes et les scores de confiance sur l'image, puis conversion en base64 pour un affichage instantané dans Dash.

---

### 2.5. Détection des Doublons & Fusion

#### ❌ Problèmes identifiés :
Le fichier `verification.py` calculait la distance géodésique (Haversine) mais n'était connecté nulle part dans le dashboard.

####  Solutions apportées :
- Connexion de `est_doublon(lat, lon, seuil_metres=50)` dans la logique d'enregistrement :
  - Si un signalement arrive à moins de 50 mètres d'un dépôt déjà existant et non nettoyé, le système affiche une alerte visuelle et propose de consolider le volume plutôt que de polluer la carte avec des marqueurs superposés.

---

## 🚀 3. Guide de Démarrage Rapide

### 1. Prérequis
- Python 3.10 ou 3.11 recommandé.
- Git.

### 2. Lancement immédiat en SQLite (recommandé)
```bash
# 1. Cloner le dépôt (privé)
git clone https://github.com/MatyDICKO/Sanuya.git
cd Sanuya

# 2. Créer l'environnement virtuel
python -m venv .venv
# Sur Windows :
.venv\Scripts\activate
# Sur Linux / macOS :
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le tableau de bord
python dashboard.py
```
Ouvrez ensuite votre navigateur sur : **`http://127.0.0.1:8050`**

### 3. Pages Disponibles
- **`http://127.0.0.1:8050/`** : Tableau de bord principal (Statistiques, Graphiques et Carte Folium interactive).
- **`http://127.0.0.1:8050/liste`** : Liste complète des dépôts avec filtres (commune, priorité, statut) et vue carte modale.
- **`http://127.0.0.1:8050/stats`** : Analyses approfondies, répartition par commune et évolution temporelle.
- **`http://127.0.0.1:8050/tester`** : Interface de test IA (upload de photo, inférence en temps réel, annotation visuelle et calcul de volume).

---

### 2.6. Tuiles Cartographiques & Résolution du Chevauchement des Modales

- **Élimination du filigrane « API KEY REQUIRED »** :
  - Le fournisseur de tuiles CartoDB exigeant désormais une clé d'API, les cartes affichaient un filigrane gênant. Remplacement par les tuiles officielles et gratuites **OpenStreetMap** (`tiles='OpenStreetMap'`), sans aucune clé requise ni restriction d'accès.
- **Résolution du chevauchement des modales sur `/liste`** :
  - Lors du chargement de la liste des dépôts, Dash initialisait les boutons d'action (`n_clicks=0`), déclenchant simultanément l'ouverture des 5 fenêtres modales (Statut, Priorité, Suppression, Photo, Carte) superposées les unes sur les autres.
  - Ajout d'un contrôle strict `if not trigger_val: return False` dans chaque callback pour garantir qu'aucune modale ne s'ouvre au chargement de la page et qu'elles ne s'ouvrent qu'après un clic explicite de l'utilisateur.
  - Harmonisation des classes CSS pour les badges de statut (`.badge-en_attente`, `.badge-en_cours`, `.badge-resolu`).

---

### 2.7. SIG Multi-Couches Avancé & Suppression des Rechargements Intempestifs

#### ❌ Problème identifié :
Sur le tableau de bord, la carte se rechargeait brutalement toutes les 5 secondes (due à l'intervalle `interval-stats` qui réécrivait la balise `iframe`). Dès que l'utilisateur tentait de zoomer, de déplacer la carte ou d'ouvrir un popup, la vue était réinitialisée au point de départ.

####  Solutions apportées :
- **Découplage des callbacks** :
  - Les 4 cartes statistiques (KPI) se mettent à jour en arrière-plan sans toucher à la carte.
  - La carte se charge proprement à l'ouverture de la page et reste parfaitement stable pendant toute la navigation.
  - Ajout d'un bouton d'actualisation manuelle dédié (*« 🔄 Actualiser la carte »*) pour recharger la cartographie à la demande sans perturbation.
- **Cartographie SIG Multi-Couches professionnelle** :
  - **Plan Standard** (OpenStreetMap officiel).
  - **🛰️ Vue Satellite HD** (Esri World Imagery) pour observer le terrain réel et les amoncellements de déchets.
  - **🏔️ Relief Topographique** (OpenTopoMap) avec courbes de niveau.
  - **🔥 HeatMap (Densité thermique)** activable en un clic pour visualiser les zones critiques d'accumulation.
  - **Mini-carte de repérage** (MiniMap) en bas à gauche et bouton **Plein Écran** (Fullscreen).
  - **Popups interactifs enrichis** : affichage de la miniature de la photo du dépôt, volume en $m^3$, niveau d'urgence, adresse géocodée et raccourci d'itinéraire GPS Google Maps.

---

### 2.8. Élimination des Éléments de Debug Parasites (Plotly Cloud & Dash DevTools)

#### ❌ Problème identifié :
Une barre violette flottante avec un bouton `<<` et un panneau surgissant *"Plotly Cloud - Install the extension to publish to Plotly Cloud (pip install dash[cloud])"* apparaissaient à l'écran. 
- *Origine :* Ce n'était pas une erreur de code, mais la barre d'outils de debug injectée par Dash (`debug=True`) faisant la promotion des services Cloud de l'éditeur Plotly.

####  Solutions apportées :
- Désactivation de l'interface graphique de debug via `dev_tools_ui=False` dans `app.run()`.
- Masquage CSS strict des sélecteurs `[class*="dash-debug"]` et `._dash-devtools` garantissant une interface 100% nette, sobre et prête pour une présentation client/direction.
- Design épuré avec la police `Inter`, palette Slate-900 / Slate-50, et suppression de la faute d'unité sur les graphiques (`m³` au lieu de `m²`).

---

## 🔒 4. Confidentialité et Données Sensibles

Conformément aux directives, le dépôt GitHub est entièrement privé entre les collaborateurs autorisés :
- La base de données de travail `sanuya.db` est directement incluse dans le suivi Git afin de permettre à votre binôme de cloner le projet et d'avoir immédiatement un environnement opérationnel sans aucune étape de configuration de serveur requise.
- Les fichiers de configuration `config.py` et les images de test sont prêts pour la collaboration immédiate.

---
*Ce rapport a été généré dans le cadre de la fiabilisation complète du projet Sanuya.*
