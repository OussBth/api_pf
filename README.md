# API de Contrôle avec FastAPI et Ansible

Ce projet est une API RESTful construite avec FastAPI qui sert d'interface pour piloter des playbooks Ansible. Elle permet d'automatiser des tâches courantes d'administration système, comme la gestion des utilisateurs Linux et la configuration de sites web Nginx, via de simples requêtes HTTP.

Le projet inclut également une interface de streaming en temps réel via WebSockets pour suivre l'exécution des playbooks.

## Fonctionnalités

* **Gestion des Utilisateurs Linux** :
    * Créer, supprimer des utilisateurs.
    * Créer des groupes.
    * Ajouter/retirer un utilisateur d'un groupe.
    * Lister les utilisateurs et les groupes (avec support de filtre par utilisateur).
* **Gestion des Sites Web (Nginx)** :
    * Créer un nouveau site (vhost) avec son dossier racine et une page d'accueil par défaut.
    * Activer / Désactiver un site.
    * Supprimer un site.
    * Lister les sites, voir leur statut et lire leur configuration.
* **Exécution en Temps Réel** :
    * Un endpoint WebSocket (`/ws/run`) pour lancer n'importe quelle action et voir la sortie d'Ansible en direct.
    * Une interface de test (`test_websocket.html`) pour interagir avec l'API de manière dynamique.

## Architecture

* **Framework API** : [FastAPI](https://fastapi.tiangolo.com/) pour sa performance et sa simplicité.
* **Serveur ASGI** : [Uvicorn](https://www.uvicorn.org/) pour exécuter l'application FastAPI.
* **Moteur d'automatisation** : [Ansible](https://www.ansible.com/) pour exécuter les tâches sur le système.
* **Structure** : L'API est découpée en `services` (logique métier), `models` (validation de données Pydantic) et `routes` (endpoints HTTP). Ansible est organisé en `rôles` pour une meilleure modularité (`linux_user`, `nginx_vhost`).

## Prérequis

* Python 3.8+
* `pip` et `venv`
* Ansible
* Nginx (installé via le playbook)
* Git

## Installation et Configuration

1.  **Cloner le dépôt**
    ```bash
    git clone (https://github.com/OussBth/api_pf.git)
    cd api_pf
    ```

2.  **Créer un environnement virtuel et l'activer**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Créer et installer les dépendances**
    D'abord, générez le fichier `requirements.txt` :
    ```bash
    pip freeze > requirements.txt
    ```
    Ensuite, pour une nouvelle installation, utilisez :
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurer Ansible Vault**
    Votre projet utilise Ansible Vault pour protéger les données sensibles.
    * Créez un fichier pour le mot de passe du coffre :
        ```bash
        # Mettez un mot de passe complexe dans ce fichier
        echo "votre_mot_de_passe_secret" > ~/.vault_pass.txt
        ```
    * Créez et chiffrez le fichier de variables :
        ```bash
        ansible-vault create vault/credentials.yml
        ```
        Ansible vous demandera le mot de passe. Vous pouvez laisser ce fichier vide pour l'instant.

5.  **Lancer le serveur API**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    L'API sera accessible sur `http://<votre_ip>:8000`.

## Utilisation de l'API

Utilisez un client comme Postman ou `curl` pour interagir avec l'API.

### Créer un site web

* **Méthode :** `POST`
* **URL :** `/api/webserver`
* **Body (JSON) :**
    ```json
    {
        "action": "create",
        "server_name": "test.monprojet.com",
        "root_dir": "/var/www/test.monprojet.com",
        "port": 8080
    }
    ```

### Lister les utilisateurs

* **Méthode :** `GET`
* **URL :** `/api/user`

### Tester le streaming en temps réel

Ouvrez le fichier `test_websocket.html` dans un navigateur pour accéder à l'interface de contrôle dynamique.

## Auteur

* **OussBth** - [Profil GitHub](https://github.com/OussBth)

## Licence

Ce projet est sous licence GPL-3.0. Voir le fichier `LICENSE` pour plus de détails.