# Rubi Studio

Plateforme complète de Prompt Engineering avec spécialités IA pour le développement web, le trading algorithmique, et l'automatisation.

## 🚀 Aperçu

Rubi Studio est une plateforme innovante qui centralise plus de 100 spécialités de prompt engineering, permettant aux utilisateurs de créer, gérer et exécuter des prompts optimisés pour diverses applications professionnelles.

## 📁 Structure du Projet

```
rubi-studio/
├── back-end/           # Backend FastAPI avec gestion des prompts et LLM
├── front-end/          # Frontend React avec design Apple (à venir)
├── trading-bot/        # Robot de trading algorithmique (à venir)
├── infrastructure/     # Infrastructure Scaleway Terraform (à venir)
└── docs/              # Documentation complète (à venir)
```

## 🎯 Fonctionnalités Principales

### Backend API
- ✅ Gestion des spécialités de prompt engineering
- ✅ Gestion des sous-spécialités et prompts experts
- ✅ Exécution de prompts avec variables dynamiques
- ✅ Support multi-LLM (OpenAI, Gemini, Claude)
- ✅ Historique d'exécution et métriques
- ✅ API RESTful complète avec FastAPI
- ✅ Base de données PostgreSQL/SQLite

### Frontend (En développement)
- 🔄 Interface utilisateur avec design Apple
- 🔄 Marketplace d'applications spécialisées
- 🔄 Éditeur de prompts avec versioning
- 🔄 Intégration N8N pour workflows
- 🔄 Dashboard analytics
- 🔄 Mode Dark/Light

### Trading Bot (En développement)
- 🔄 Trading algorithmique avec CCXT
- 🔄 Analyse technique avec TA-Lib
- 🔄 Monitoring Prometheus/Grafana
- 🔄 Stratégies personnalisables

## 🏗️ Technologies

- **Backend:** FastAPI, SQLAlchemy, Pydantic, Python 3.11
- **Frontend:** React 18, Vite, Tailwind CSS, TypeScript
- **Base de données:** PostgreSQL, Redis
- **Trading:** CCXT, Pandas, NumPy, TA-Lib
- **Infrastructure:** Terraform, Scaleway, Docker
- **Monitoring:** Prometheus, Grafana

## 🚀 Démarrage Rapide

### Backend

```bash
cd back-end
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Accédez à l'API : http://localhost:8000/docs

### Frontend (À venir)

```bash
cd front-end
pnpm install
pnpm dev
```

## 📚 Documentation

- [Backend README](back-end/README.md)
- [Guide de Déploiement](docs/DEPLOYMENT_GUIDE.md) (à venir)
- [Architecture](docs/ARCHITECTURE.md) (à venir)

## 🎨 Design

Le design de Rubi Studio s'inspire des Human Interface Guidelines d'Apple, offrant une expérience utilisateur élégante et intuitive avec :
- Mode Dark/Light
- Animations fluides
- Composants réutilisables
- Accessibilité WCAG 2.1 AA

## 💰 Infrastructure

Infrastructure complète sur Scaleway :
- Backend (GP1-S: 4 vCPU, 8GB RAM)
- Frontend (DEV1-M: 3 vCPU, 4GB RAM)
- Trading Bot (GP1-M: 8 vCPU, 16GB RAM)
- PostgreSQL + Redis
- Load Balancer avec SSL
- Object Storage S3

**Coût estimé :** ~€171/mois

## 🔐 Sécurité

- Authentification JWT
- Gestion des secrets sécurisée
- HTTPS/SSL avec Let's Encrypt
- Security Groups configurés
- Backups automatiques

## 📊 Spécialités Disponibles

Plus de 100 spécialités organisées par domaines :
- 🌐 Développement Web & Applications
- 🎨 Design & UX
- 🔒 Sécurité & Conformité
- 💹 Finance & Trading
- 💳 Paiements & Banking
- ☁️ Infrastructure & Cloud
- 🛒 E-Commerce & Marketing
- 🎨 IA Générative
- 🎮 Gaming & Esports
- 🏥 Secteurs Verticaux
- ⚛️ Technologies Avancées

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez notre guide de contribution (à venir).

## 📄 Licence

Propriétaire - Rubi Studio © 2025

## 👥 Équipe

Développé avec ❤️ par l'équipe Rubi Studio

## 📞 Contact

- Website: https://rubi-studio.com (à venir)
- Email: contact@rubi-studio.com
- GitHub: https://github.com/pivori-app/rubi-studio

---

**Version:** 1.0.0  
**Dernière mise à jour:** 22 Octobre 2025
