# 🤖 Rubi Studio - Intégration MT5 Trading

**Version :** 3.0.0  
**Date :** 23 Octobre 2025  
**Objectif :** Le backend doit recevoir correctement les signaux du robot de trading MT5

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Utilisation](#utilisation)
6. [API Documentation](#api-documentation)
7. [Tests](#tests)
8. [Déploiement](#déploiement)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Vue d'Ensemble

Cette intégration permet à Rubi Studio de recevoir et gérer les signaux de trading depuis MetaTrader 5 (MT5) en temps réel.

### ✨ Fonctionnalités

- ✅ **Connexion MT5 ↔ Backend** : Communication bidirectionnelle
- ✅ **Réception des signaux** : BUY, SELL, CLOSE_BUY, CLOSE_SELL
- ✅ **Exécution automatique** : Ordres exécutés automatiquement
- ✅ **Suivi des positions** : Positions ouvertes en temps réel
- ✅ **Historique complet** : Tous les trades stockés en base
- ✅ **WebSocket** : Mises à jour en temps réel
- ✅ **Risk Management** : Calcul automatique du volume
- ✅ **Logging structuré** : Logs JSON pour analyse
- ✅ **Monitoring** : Statistiques et métriques
- ✅ **Scalabilité** : Architecture prête pour la production

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ARCHITECTURE GLOBALE                         │
└─────────────────────────────────────────────────────────────────┘

MT5 Terminal (Windows/Wine)
         │
         │ MQL5 Script (RubiStudioConnector.mq5)
         │ - Monitoring positions
         │ - Envoi signaux HTTP
         │ - Réception ordres
         ↓
┌──────────────────────────────────────────────────────────────────┐
│                    RUBI STUDIO BACKEND                            │
│                                                                   │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │  FastAPI        │◄────►│  WebSocket      │                   │
│  │  REST API       │      │  Real-time      │                   │
│  └────────┬────────┘      └─────────────────┘                   │
│           │                                                       │
│           ↓                                                       │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │  Signal         │      │  Position       │                   │
│  │  Processor      │      │  Tracker        │                   │
│  └────────┬────────┘      └────────┬────────┘                   │
│           │                        │                             │
│           ↓                        ↓                             │
│  ┌──────────────────────────────────────────┐                   │
│  │         PostgreSQL Database               │                   │
│  │  - trading_signals                        │                   │
│  │  - trading_orders                         │                   │
│  │  - trading_positions                      │                   │
│  │  - mt5_sessions                           │                   │
│  │  - account_snapshots (TimescaleDB)        │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                   │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │  Redis Cache    │      │  Celery Queue   │                   │
│  │  - Sessions     │      │  - Async tasks  │                   │
│  └─────────────────┘      └─────────────────┘                   │
└──────────────────────────────────────────────────────────────────┘
         │
         │ Logs & Metrics
         ↓
┌──────────────────────────────────────────────────────────────────┐
│                    MONITORING & LOGGING                           │
│  - Prometheus                                                     │
│  - Grafana                                                        │
│  - ELK Stack                                                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prérequis

- **Python** 3.11+
- **PostgreSQL** 15+ (avec TimescaleDB)
- **Redis** 7.0+
- **MT5 Terminal** (Windows ou Wine sur Linux)

### 1. Cloner le Repository

```bash
git clone https://github.com/pivori-app/rubi-studio.git
cd rubi-studio/mt5-integration
```

### 2. Installer les Dépendances Python

```bash
cd python-api
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Configurer la Base de Données

```bash
cd ../database

# Installer PostgreSQL (si nécessaire)
# Sur Ubuntu/Debian:
sudo apt-get install postgresql-15 postgresql-contrib

# Créer la base de données
sudo -u postgres psql
CREATE DATABASE rubi_trading;
CREATE USER rubi_admin WITH PASSWORD 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE rubi_trading TO rubi_admin;
\q

# Exécuter le schéma
psql -U rubi_admin -d rubi_trading -f schema.sql
```

### 4. Installer MT5 Connector

#### Sur Windows

1. Télécharger et installer MT5
2. Copier `mql5/RubiStudioConnector.mq5` dans `C:\Program Files\MetaTrader 5\MQL5\Experts\`
3. Compiler le script dans MetaEditor
4. Attacher l'Expert Advisor à un graphique

#### Sur Linux (avec Wine)

```bash
# Installer Wine
sudo apt-get install wine64

# Télécharger MT5
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

# Installer MT5
wine mt5setup.exe

# Copier le script
cp mql5/RubiStudioConnector.mq5 ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/MQL5/Experts/
```

---

## ⚙️ Configuration

### 1. Variables d'Environnement

Créer un fichier `.env` dans `python-api/` :

```bash
# Database
DATABASE_URL=postgresql://rubi_admin:YOUR_PASSWORD@localhost:5432/rubi_trading

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-change-in-production

# JWT
JWT_SECRET=your-jwt-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://app.rubi-studio.com"]

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=

# Monitoring
PROMETHEUS_PORT=9090
```

### 2. Configuration MT5

Dans MT5, configurer l'Expert Advisor :

- **BackendURL** : `https://api.rubi-studio.com` (ou `http://localhost:8000` pour dev)
- **APIToken** : Votre token API (généré depuis le backend)
- **CheckInterval** : 5000 (ms)
- **EnableAutoTrading** : true
- **MaxRiskPercent** : 2.0
- **MaxOpenPositions** : 5

### 3. Autoriser WebRequest dans MT5

1. Ouvrir MT5
2. Aller dans `Tools` → `Options` → `Expert Advisors`
3. Cocher `Allow WebRequest for listed URL`
4. Ajouter : `https://api.rubi-studio.com` (ou votre URL)

---

## 🚀 Utilisation

### 1. Lancer l'API Backend

```bash
cd python-api
source venv/bin/activate

# Mode développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Mode production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. Vérifier l'API

```bash
# Health check
curl http://localhost:8000/health

# Documentation
open http://localhost:8000/docs
```

### 3. Générer un Token API

```bash
# Via l'API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trader@example.com",
    "username": "trader1",
    "password": "SecurePassword123!"
  }'

# Récupérer le token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "password": "SecurePassword123!"
  }'
```

### 4. Lancer MT5 Connector

1. Ouvrir MT5
2. Ouvrir un graphique (ex: EURUSD H1)
3. Glisser-déposer `RubiStudioConnector` sur le graphique
4. Configurer les paramètres
5. Cliquer sur `OK`

### 5. Vérifier la Connexion

```bash
# Vérifier les sessions actives
curl -X GET http://localhost:8000/api/v1/mt5/sessions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Vérifier les signaux
curl -X GET http://localhost:8000/api/v1/trading/signals \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 API Documentation

### Endpoints Principaux

#### 🔌 MT5 Connection

```bash
# Connexion
POST /api/v1/mt5/connect
Body: {
  "account_number": "12345678",
  "broker": "IC Markets",
  "balance": 10000.00,
  "equity": 10000.00,
  "currency": "USD"
}

# Ping
POST /api/v1/mt5/ping
Body: {
  "session_id": "uuid",
  "timestamp": "2025-10-23T10:00:00Z",
  "balance": 10050.00,
  "equity": 10050.00,
  "margin_free": 9000.00
}

# Déconnexion
POST /api/v1/mt5/disconnect
Body: {
  "session_id": "uuid",
  "timestamp": "2025-10-23T18:00:00Z",
  "total_signals_sent": 10,
  "total_signals_received": 5,
  "total_orders_executed": 5,
  "total_errors": 0
}
```

#### 📊 Trading Signals

```bash
# Recevoir un signal
POST /api/v1/trading/signals
Body: {
  "symbol": "EURUSD",
  "signal_type": "BUY",
  "entry_price": 1.1000,
  "stop_loss": 1.0950,
  "take_profit": 1.1100,
  "volume": 0.1,
  "timeframe": "H1",
  "confidence": 0.8,
  "signal_time": "2025-10-23T10:00:00Z"
}

# Récupérer les signaux
GET /api/v1/trading/signals?symbol=EURUSD&status=PENDING&limit=100

# Récupérer les signaux en attente
GET /api/v1/trading/signals/pending?session_id=uuid

# Mettre à jour le statut
POST /api/v1/trading/signals/{signal_id}/status
Body: {
  "signal_id": 1,
  "status": "EXECUTED",
  "message": "Order ticket: 123456789",
  "timestamp": "2025-10-23T10:01:00Z"
}
```

#### 📈 Positions

```bash
# Mettre à jour les positions
POST /api/v1/trading/positions/update
Body: {
  "session_id": "uuid",
  "timestamp": "2025-10-23T10:00:00Z",
  "positions": [
    {
      "ticket": "123456789",
      "symbol": "EURUSD",
      "type": "BUY",
      "volume": 0.1,
      "open_price": 1.1000,
      "current_price": 1.1020,
      "sl": 1.0950,
      "tp": 1.1100,
      "profit": 20.00,
      "swap": 0.00,
      "commission": -0.70,
      "open_time": "2025-10-23T10:00:00Z"
    }
  ]
}

# Récupérer les positions
GET /api/v1/trading/positions?session_id=uuid
```

#### 💰 Account Info

```bash
# Mettre à jour les infos du compte
POST /api/v1/mt5/account/update
Body: {
  "session_id": "uuid",
  "balance": 10050.00,
  "equity": 10070.00,
  "margin": 100.00,
  "margin_free": 9970.00,
  "margin_level": 10070.00,
  "profit": 20.00
}

# Récupérer les infos du compte
GET /api/v1/mt5/account/{session_id}
```

#### 📊 Statistics

```bash
# Statistiques globales
GET /api/v1/stats
Response: {
  "signals": {
    "total": 100,
    "executed": 85,
    "pending": 10,
    "rejected": 5
  },
  "sessions": {
    "active": 3,
    "total": 10
  },
  "positions": {
    "open": 5
  }
}
```

### WebSocket

```javascript
// Connexion WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/trading/live/session_id');

ws.onopen = () => {
  console.log('Connected');
  // Ping
  ws.send(JSON.stringify({ type: 'ping' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

## 🧪 Tests

```bash
# Installer les dépendances de test
pip install pytest pytest-asyncio pytest-cov httpx

# Lancer les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=. --cov-report=html

# Ouvrir le rapport de couverture
open htmlcov/index.html
```

---

## 🚀 Déploiement sur Scaleway

Voir le guide complet : [database/scaleway_database_setup.md](database/scaleway_database_setup.md)

### Résumé

```bash
# 1. Provisionner l'infrastructure
cd scaleway_infrastructure/terraform
terraform init
terraform apply

# 2. Installer la base de données
cd ../../mt5-integration/database
./install_database.sh YOUR_DB_PASSWORD

# 3. Déployer l'API
cd ../python-api
# Configurer .env avec les credentials Scaleway
docker build -t rubi-studio-api .
docker push registry.scaleway.com/rubi-studio/api:latest

# 4. Déployer sur Kubernetes
kubectl apply -f k8s/
```

---

## 📊 Monitoring

### Prometheus Metrics

```bash
# Accéder aux métriques
curl http://localhost:8000/metrics
```

### Grafana Dashboards

1. Importer le dashboard `monitoring/grafana-dashboard.json`
2. Configurer la source de données Prometheus
3. Visualiser les métriques en temps réel

### Logs

```bash
# Logs structurés JSON
tail -f logs/rubi-studio.log | jq .

# Rechercher des erreurs
grep "ERROR" logs/rubi-studio.log | jq .
```

---

## 🔧 Troubleshooting

### Problème : MT5 ne se connecte pas au backend

**Solution :**
1. Vérifier que l'URL est autorisée dans MT5 (`Tools` → `Options` → `Expert Advisors`)
2. Vérifier le token API
3. Vérifier les logs MT5 (`Experts` tab)

### Problème : Signaux non reçus

**Solution :**
1. Vérifier que l'EA est actif (sourire vert dans le coin supérieur droit)
2. Vérifier les logs backend : `tail -f logs/rubi-studio.log`
3. Tester manuellement avec curl

### Problème : Ordres non exécutés

**Solution :**
1. Vérifier que `EnableAutoTrading` est `true`
2. Vérifier que le trading automatique est autorisé dans MT5
3. Vérifier le solde et la marge disponible
4. Vérifier les logs MT5

---

## 📞 Support

- **Email :** support@rubi-studio.com
- **Documentation :** https://docs.rubi-studio.com
- **GitHub Issues :** https://github.com/pivori-app/rubi-studio/issues

---

## 📄 Licence

Copyright © 2025 Rubi Studio. Tous droits réservés.

---

**Auteur :** Expert Architecte Senior Backend  
**Version :** 3.0.0  
**Date :** 23 Octobre 2025

