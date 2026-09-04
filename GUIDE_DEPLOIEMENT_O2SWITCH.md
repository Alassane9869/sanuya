# Guide de Déploiement SANUYA sur o2switch (cPanel)

Ce guide détaille la mise en production de **SANUYA** sur l'hébergement o2switch pour le sous-domaine **`sanuya.danayaplus.com`**.

---

## 1. Récapitulatif des identifiants & configuration

* **Domaine** : `sanuya.danayaplus.com`
* **Compte cPanel** : `vuxe8870`
* **Base de données MySQL** : `vuxe8870_sanuya`
* **Utilisateur MySQL** : `vuxe8870_sanuya_bko`
* **Mot de passe** : `%ri-l5ac8J?ahGGN`
* **Hôte MySQL (sur le serveur o2switch)** : `localhost` (Port 3306)

---

## 2. Étape 1 : Initialiser la Base de Données dans phpMyAdmin

1. Connectez-vous à votre **cPanel o2switch**.
2. Dans la section **Bases de données**, cliquez sur **phpMyAdmin**.
3. Dans la colonne de gauche, cliquez sur la base **`vuxe8870_sanuya`**.
4. Cliquez sur l'onglet supérieur **Importer**.
5. Cliquez sur **Choisir un fichier** et sélectionnez le fichier **`deploy_o2switch.sql`** (situé à la racine du projet).
6. Cliquez sur le bouton **Exécuter** tout en bas.
   > ✅ La table `signalements` et les données initiales sont créées.

---

## 3. Étape 2 : Envoyer les fichiers du projet sur o2switch

Vous pouvez utiliser soit **Git Version Control** de cPanel, soit le **Gestionnaire de fichiers** (ou FTP/FileZilla) :

1. Dans cPanel, ouvrez le **Gestionnaire de fichiers**.
2. Créez un dossier dédié à la racine de votre compte (par exemple `/home/vuxe8870/sanuya/` ou dans le dossier associé au sous-domaine `sanuya.danayaplus.com`).
3. Téléversez l'ensemble des fichiers du projet dans ce dossier :
   - `dashboard.py`, `database.py`, `config.py`
   - `passenger_wsgi.py` *(essentiel pour o2switch)*
   - `requirements.txt`
   - Les modèles `yolov8n.pt`, `yolov8m.pt`
   - Les dossiers `images_test/`, `assets/` (si présents)

---

## 4. Étape 3 : Créer l'application Python dans cPanel

1. Dans votre cPanel, cherchez et cliquez sur **« Configurer une application Python »** (*Setup Python App*).
2. Cliquez sur **Créer une application** (*Create Application*).
3. Remplissez les champs suivants :
   * **Version de Python** : Sélectionnez **3.10** ou **3.11**.
   * **Application root (Racine de l'application)** : Le chemin de votre dossier (ex: `sanuya` ou le chemin complet).
   * **Application URL** : Choisissez `sanuya.danayaplus.com` dans la liste déroulante.
   * **Application startup file** : Indiquez **`passenger_wsgi.py`**.
   * **Application Entry point** : Indiquez **`application`**.
4. Cliquez sur le bouton **Créer** (*Create*) en haut à droite.

---

## 5. Étape 4 : Installer les dépendances (pip)

Une fois l'application créée dans cPanel :
1. Sur la page de configuration de l'application, repérez la commande affichée en haut pour activer l'environnement virtuel, par exemple :
   ```bash
   source /home/vuxe8870/virtualenv/sanuya/3.11/bin/activate && cd /home/vuxe8870/sanuya
   ```
2. Dans la section **Configuration files** :
   * Tapez `requirements.txt` puis cliquez sur **Add**.
   * Cliquez ensuite sur le bouton **Run Pip Install**.
3. *Alternative par Terminal cPanel / SSH* :
   Ouvrez le **Terminal** cPanel, collez la commande d'activation ci-dessus, puis lancez :
   ```bash
   pip install -r requirements.txt
   ```

---

## 6. Étape 5 : Redémarrer et Tester

1. Dans l'interface **Setup Python App**, cliquez sur **Restart** (bouton avec l'icône de flèche circulaire).
2. Ouvrez votre navigateur et accédez à :  
   👉 **`https://sanuya.danayaplus.com`**
3. L'application Dash se charge et se connecte automatiquement à la base MySQL `vuxe8870_sanuya` en local sur le serveur o2switch.

---

## 7. Points d'attention spécifiques o2switch

* **OpenCV headless** : Sur o2switch, les bibliothèques d'affichage X11 (`libGL.so`) ne sont pas présentes. C'est pourquoi nous utilisons `opencv-python-headless` dans `requirements.txt` pour éviter toute erreur de chargement.
* **Redémarrage après modification** : Chaque fois que vous modifiez un fichier Python (`dashboard.py`, `config.py`), cliquez sur **Restart** dans la page Python App pour recharger le processus Passenger.
