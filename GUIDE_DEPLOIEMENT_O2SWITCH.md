# Guide de Déploiement SANUYA sur o2switch (Automatisé à 100%)

Ce guide détaille la mise en production de **SANUYA** sur l'hébergement o2switch pour **`sanuya.danayaplus.com`**.

> 💡 **ZÉRO MANIPULATION PHPMYADMIN REQUISE** :  
> Le script `deploy_o2switch.py` installe automatiquement toutes les dépendances pip, crée les tables MySQL, migre l'ensemble des données et redémarre l'application.

---

## 1. Identifiants & Configuration Déjà Intégrés

* **Sous-domaine** : `sanuya.danayaplus.com`
* **Compte cPanel** : `vuxe8870`
* **Base MySQL** : `vuxe8870_sanuya`
* **Utilisateur MySQL** : `vuxe8870_sanuya_bko`
* **Mot de passe** : `%ri-l5ac8J?ahGGN`
* **Hôte** : `localhost`

---

## 2. Procédure Ultra-Simple (3 Étapes)

### Étape 1 : Cloner le projet sur cPanel (Git Version Control)
1. Dans votre cPanel o2switch, ouvrez **Git Version Control**.
2. Cliquez sur **Create**.
3. Remplissez :
   * **Clone URL** : `https://github.com/Alassane9869/sanuya.git`
   * **Repository Path** : `sanuya` (ou le chemin de votre sous-domaine)
   * **Branch** : `main`
4. Cliquez sur **Create** pour cloner le code.

---

### Étape 2 : Créer l'Application Python dans cPanel
1. Allez dans **« Configurer une application Python »** (*Setup Python App*).
2. Cliquez sur **Créer une application** :
   * **Version de Python** : `3.10` ou `3.11`
   * **Application root** : `sanuya`
   * **Application URL** : Sélectionnez `sanuya.danayaplus.com`
   * **Application startup file** : `passenger_wsgi.py`
   * **Application Entry point** : `application`
3. Cliquez sur **Créer**.

---

### Étape 3 : Lancer le Déploiement & Migration Automatique (1 seule commande)

1. Ouvrez le **Terminal** de cPanel (ou connectez-vous en SSH).
2. Activez l'environnement virtuel et placez-vous dans le dossier (en copiant la commande indiquée en haut de votre page Python App, par exemple) :
   ```bash
   source /home/vuxe8870/virtualenv/sanuya/3.11/bin/activate && cd /home/vuxe8870/sanuya
   ```
3. Lancez le script tout-en-un :
   ```bash
   python deploy_o2switch.py
   ```
   *(ou `bash deploy.sh`)*

**Ce que le script fait automatiquement en quelques secondes :**
* ✅ Met à jour pip et installe toutes les dépendances requises (`dash`, `opencv-python-headless`, `yolo`, `mysql-connector-python`, `reportlab`, etc.).
* ✅ Se connecte à la base `vuxe8870_sanuya` et crée la table `signalements` avec tous les index optimisés.
* ✅ Migre toutes les données réelles de signalements directement dans MySQL.
* ✅ Notifie Passenger (`tmp/restart.txt`) pour redémarrer l'application.

---

## 3. Accès à la Plateforme

Ouvrez simplement votre navigateur sur :  
👉 **`https://sanuya.danayaplus.com`**

> 🔄 **Vérification / Synchronisation Web de secours** :  
> Si besoin, l'URL suivante permet aussi de relancer la synchronisation directement depuis n'importe quel navigateur :  
> `https://sanuya.danayaplus.com/api/migrate`
