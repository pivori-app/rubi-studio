# Rubi Studio Backend API - Version 2.0

Backend FastAPI amélioré avec corrections critiques et fonctionnalités avancées.

## 🚀 Nouvelles Fonctionnalités (v2.0)

### ✅ Corrections Critiques

1. **Exécution Réelle des Prompts avec LLM**
   - Intégration complète OpenAI, Gemini, Claude
   - Abstraction unifiée des providers LLM
   - Calcul automatique des coûts

2. **Validation des Variables**
   - Validation robuste avec jsonschema
   - Messages d'erreur détaillés
   - Enrichissement avec valeurs par défaut

3. **Authentification JWT**
   - Endpoints register/login
   - Protection des routes sensibles
   - Gestion des tokens

4. **Historique d'Exécution Complet**
   - Enregistrement de toutes les exécutions
   - Endpoints de consultation
   - Filtres par prompt, statut, date

5. **Métriques Prometheus**
   - Métriques détaillées (exécutions, tokens, coûts)
   - Endpoint /metrics
   - Prêt pour Grafana

### 🎯 Fonctionnalités Principales

- **Gestion des Spécialités** : CRUD complet pour specialties, sub-specialties, expert prompts
- **Support Multi-LLM** : OpenAI (GPT-4, GPT-3.5), Gemini (Pro, Flash), Claude (Opus, Sonnet, Haiku)
- **Validation Avancée** : Validation des variables contre schémas JSON
- **Sécurité** : Authentification JWT, hachage bcrypt
- **Monitoring** : Métriques Prometheus, logging structuré
- **Base de Données** : Support PostgreSQL et SQLite

## 📋 Prérequis

- Python 3.11+
- PostgreSQL 15+ (recommandé) ou SQLite (développement)
- Redis 7+ (pour Celery, optionnel)
- Clés API pour les LLM :
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY`
  - `ANTHROPIC_API_KEY`

## 🛠️ Installation

### 1. Cloner le repository

```bash
git clone https://github.com/pivori-app/rubi-studio.git
cd rubi-studio/back-end-v2
```

### 2. Créer un environnement virtuel

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Créer un fichier `.env` :

```env
# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/rubi_studio
# ou pour SQLite (développement)
# DATABASE_URL=sqlite:///./rubi_studio.db

# JWT
JWT_SECRET=your-secret-key-change-in-production

# LLM API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...

# Redis (optionnel, pour Celery)
REDIS_URL=redis://localhost:6379/0
```

### 5. Initialiser la base de données

```bash
# Avec Alembic (recommandé)
alembic upgrade head

# Ou laisser SQLAlchemy créer les tables automatiquement au démarrage
```

## 🚀 Démarrage

### Mode Développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Mode Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Avec Gunicorn (Production)

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📚 Documentation API

Une fois le serveur démarré, accédez à :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **Métriques Prometheus** : http://localhost:8000/metrics
- **Health Check** : http://localhost:8000/health

## 🔐 Authentification

### 1. Créer un compte

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "password": "securepassword"
  }'
```

### 2. Se connecter

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

Réponse :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Utiliser le token

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <votre-token>"
```

## 🎯 Exemples d'Utilisation

### Créer une Spécialité

```bash
curl -X POST "http://localhost:8000/api/v1/specialties" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Développement Web",
    "description": "Spécialité en développement web full-stack",
    "icon_url": "https://example.com/icon.png"
  }'
```

### Créer un Prompt Expert

```bash
curl -X POST "http://localhost:8000/api/v1/expert-prompts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sub_specialty_id": 1,
    "title": "Créer une API REST",
    "template": "Créer une API REST avec {framework} pour {use_case}",
    "variables_schema": {
      "type": "object",
      "properties": {
        "framework": {
          "type": "string",
          "enum": ["FastAPI", "Express", "Django"],
          "description": "Framework web à utiliser"
        },
        "use_case": {
          "type": "string",
          "description": "Cas d'\''utilisation de l'\''API"
        }
      },
      "required": ["framework", "use_case"]
    },
    "expected_output": "Code source complet de l'\''API"
  }'
```

### Exécuter un Prompt

```bash
curl -X POST "http://localhost:8000/api/v1/execute-prompt/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "framework": "FastAPI",
      "use_case": "gestion de tâches"
    },
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "temperature": 0.7
  }'
```

Réponse :
```json
{
  "execution_id": 123,
  "prompt_id": 1,
  "output": "Voici le code complet de l'API...",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "tokens_used": 1500,
  "cost": 0.045,
  "execution_time": 3.2,
  "status": "success"
}
```

### Consulter l'Historique

```bash
curl -X GET "http://localhost:8000/api/v1/executions/history?limit=10" \
  -H "Authorization: Bearer <token>"
```

## 🧪 Tests

```bash
# Installer les dépendances de test
pip install pytest pytest-asyncio pytest-cov httpx

# Lancer les tests
pytest

# Avec couverture
pytest --cov=app --cov-report=html
```

## 📊 Monitoring

### Métriques Prometheus

Le endpoint `/metrics` expose les métriques suivantes :

- `prompt_executions_total` : Nombre total d'exécutions
- `prompt_execution_duration_seconds` : Durée des exécutions
- `llm_tokens_used_total` : Tokens utilisés par LLM
- `llm_cost_total_usd` : Coût total en USD
- `active_executions` : Nombre d'exécutions actives

### Configuration Grafana

Importer le dashboard Grafana depuis `grafana/dashboard.json` (à créer).

## 🔧 Configuration Avancée

### PostgreSQL

```bash
# Créer la base de données
createdb rubi_studio

# Configurer l'URL
export DATABASE_URL=postgresql://user:password@localhost:5432/rubi_studio
```

### Redis (pour Celery)

```bash
# Démarrer Redis
redis-server

# Démarrer Celery worker
celery -A app.celery_app worker --loglevel=info
```

## 📝 Structure du Projet

```
back-end-v2/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application FastAPI principale
│   ├── models.py            # Modèles SQLAlchemy
│   ├── schemas.py           # Schémas Pydantic
│   ├── database.py          # Configuration base de données
│   ├── llm_providers.py     # Abstraction des LLM
│   └── validators.py        # Validation des variables
├── requirements.txt         # Dépendances Python
└── README.md               # Ce fichier
```

## 🐛 Dépannage

### Erreur "OPENAI_API_KEY not set"

Assurez-vous d'avoir configuré les variables d'environnement :

```bash
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...
export ANTHROPIC_API_KEY=sk-ant-...
```

### Erreur de connexion PostgreSQL

Vérifiez que PostgreSQL est démarré et que l'URL est correcte :

```bash
psql -U user -d rubi_studio -h localhost
```

### Erreur "Could not validate credentials"

Le token JWT a expiré. Reconnectez-vous pour obtenir un nouveau token.

## 📄 Licence

Propriétaire - Rubi Studio © 2025

## 👥 Contributeurs

- Équipe Rubi Studio

## 📞 Support

Pour toute question ou problème, ouvrez une issue sur GitHub.

