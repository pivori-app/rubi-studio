# Rubi Studio Prompt Engineering API

Ce projet implémente une API backend pour gérer les spécialités de Prompt Engineering, les sous-spécialités, les prompts experts, et les experts associés pour Rubi Studio. Il utilise FastAPI, SQLAlchemy et PostgreSQL (ou SQLite pour le développement local).

## Structure du Projet

```
rubi_studio_backend/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── database.py
└── README.md
```

*   `main.py`: Le point d'entrée principal de l'application FastAPI, définissant les routes de l'API.
*   `models.py`: Définit les modèles de base de données SQLAlchemy pour les spécialités, sous-spécialités, prompts experts, experts et leurs associations.
*   `schemas.py`: Définit les schémas de données Pydantic pour la validation des requêtes et des réponses de l'API.
*   `database.py`: Contient la configuration de la base de données et la session SQLAlchemy.

## Installation

1.  **Cloner le dépôt :**
    ```bash
    git clone <URL_DU_DEPOT>
    cd rubi_studio_backend
    ```

2.  **Installer les dépendances Python :**
    ```bash
    pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary
    ```
    *(Note: `psycopg2-binary` est pour PostgreSQL. Si vous utilisez SQLite pour le développement local, vous n'en avez pas besoin, mais il est inclus pour la compatibilité future avec PostgreSQL.)*

## Exécution de l'API

Pour lancer l'application FastAPI, exécutez la commande suivante depuis le répertoire `rubi_studio_backend` :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

L'option `--reload` est utile pour le développement car elle redémarre le serveur à chaque modification de fichier.

## Accès à l'API

Une fois l'API en cours d'exécution, vous pouvez y accéder via votre navigateur ou un outil comme `curl` ou Postman.

*   **Point d'entrée racine :**
    `http://localhost:8000/`
    Vous devriez voir : `{"message": "Welcome to Rubi Studio Prompt Engineering API"}`

*   **Documentation interactive (Swagger UI) :**
    `http://localhost:8000/docs`
    Cette interface vous permet de visualiser tous les points de terminaison de l'API, de tester les requêtes et de comprendre les schémas de données.

*   **Documentation OpenAPI (JSON) :**
    `http://localhost:8000/openapi.json`
    Ce fichier contient la spécification OpenAPI de l'API, utile pour la génération de clients ou l'intégration avec d'autres outils.

## Points de Terminaison Clés de l'API

L'API expose les points de terminaison suivants pour gérer les entités :

*   `/specialties/`: Gère les opérations CRUD pour les spécialités.
*   `/sub_specialties/`: Gère les opérations CRUD pour les sous-spécialités.
*   `/expert_prompts/`: Gère les opérations CRUD pour les prompts experts.
*   `/experts/`: Gère les opérations CRUD pour les experts.
*   `/expert_prompt_associations/`: Gère les associations entre experts et prompts experts.
*   `/execute-prompt/{prompt_id}`: Permet d'exécuter un prompt expert en fournissant les variables nécessaires.

## Intégration avec des Outils de Workflow (comme N8N)

L'API est conçue pour être facilement intégrable avec des outils de workflow. Le point de terminaison `/execute-prompt/{prompt_id}` est particulièrement pertinent :

1.  **Récupérer les schémas de variables :** Utilisez les points de terminaison `GET /expert_prompts/{prompt_id}` pour récupérer le `variables_schema` d'un prompt expert. Ce schéma peut être utilisé par l'outil de workflow pour générer dynamiquement un formulaire de saisie pour l'utilisateur.
2.  **Exécuter le prompt :** Envoyez une requête `POST` à `/execute-prompt/{prompt_id}` avec les variables renseignées par l'utilisateur. Le backend gérera l'injection des variables et l'appel au modèle LLM.
3.  **Traiter la sortie :** L'API retournera la sortie du modèle LLM, qui pourra être utilisée par l'outil de workflow pour des actions ultérieures (par exemple, envoyer un e-mail, créer une tâche, etc.).

## Développement

Pour le développement, la base de données est configurée pour utiliser SQLite (`sql_app.db`). Pour une utilisation en production, il est recommandé de configurer une base de données PostgreSQL et de mettre à jour la variable `SQLALCHEMY_DATABASE_URL` dans `app/database.py` en conséquence.

```python
# Exemple pour PostgreSQL
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
```

Assurez-vous que la base de données est créée et que les migrations sont appliquées si vous utilisez un système de migration comme Alembic (non inclus dans ce MVP).

