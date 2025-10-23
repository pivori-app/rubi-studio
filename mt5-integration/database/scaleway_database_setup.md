# Configuration Base de Données PostgreSQL sur Scaleway pour Rubi Studio Trading

**Date :** 23 Octobre 2025  
**Version :** 3.0.0  
**Objectif :** Stocker tous les trades, signaux, positions et données de trading MT5

---

## 📋 Table des Matières

1. [Architecture de la Base de Données](#architecture-de-la-base-de-données)
2. [Provisionnement sur Scaleway](#provisionnement-sur-scaleway)
3. [Schéma SQL Complet](#schéma-sql-complet)
4. [Configuration PostgreSQL](#configuration-postgresql)
5. [Extensions PostgreSQL](#extensions-postgresql)
6. [Indexes et Optimisations](#indexes-et-optimisations)
7. [Backups et Réplication](#backups-et-réplication)
8. [Monitoring et Maintenance](#monitoring-et-maintenance)
9. [Migration depuis SQLite](#migration-depuis-sqlite)
10. [Scripts d'Installation](#scripts-dinstallation)

---

## 1. Architecture de la Base de Données

### 📊 Schéma Relationnel

```
┌─────────────────────────────────────────────────────────────────┐
│                     RUBI STUDIO TRADING DATABASE                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│      users       │         │  trading_        │
│                  │         │  strategies      │
│  - id (PK)       │◄────────┤  - id (PK)       │
│  - email         │         │  - user_id (FK)  │
│  - username      │         │  - name          │
│  - password_hash │         │  - config        │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         │                            │
         ▼                            ▼
┌──────────────────┐         ┌──────────────────┐
│  mt5_sessions    │         │  trading_        │
│                  │         │  signals         │
│  - id (PK)       │         │  - id (PK)       │
│  - user_id (FK)  │         │  - user_id (FK)  │
│  - session_id    │         │  - strategy_id   │
│  - account_no    │         │  - symbol        │
│  - broker        │         │  - signal_type   │
│  - is_active     │         │  - status        │
└──────────────────┘         │  - entry_price   │
                              │  - stop_loss     │
                              │  - take_profit   │
                              │  - volume        │
                              └────────┬─────────┘
                                       │
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  trading_        │
                              │  orders          │
                              │  - id (PK)       │
                              │  - signal_id (FK)│
                              │  - user_id (FK)  │
                              │  - mt5_order_id  │
                              │  - symbol        │
                              │  - order_type    │
                              │  - volume        │
                              │  - open_price    │
                              │  - close_price   │
                              │  - profit        │
                              │  - commission    │
                              │  - swap          │
                              └──────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  trading_        │         │  account_        │
│  positions       │         │  snapshots       │
│  - id (PK)       │         │  - id (PK)       │
│  - session_id    │         │  - session_id    │
│  - ticket        │         │  - balance       │
│  - symbol        │         │  - equity        │
│  - type          │         │  - margin        │
│  - volume        │         │  - profit        │
│  - open_price    │         │  - timestamp     │
│  - current_price │         └──────────────────┘
│  - profit        │
│  - updated_at    │
└──────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  market_data     │         │  performance_    │
│  (TimescaleDB)   │         │  metrics         │
│  - id (PK)       │         │  - id (PK)       │
│  - symbol        │         │  - user_id (FK)  │
│  - timeframe     │         │  - strategy_id   │
│  - timestamp     │         │  - total_trades  │
│  - open          │         │  - win_rate      │
│  - high          │         │  - total_profit  │
│  - low           │         │  - max_drawdown  │
│  - close         │         │  - sharpe_ratio  │
│  - volume        │         │  - calculated_at │
└──────────────────┘         └──────────────────┘
```

---

## 2. Provisionnement sur Scaleway

### 📦 Configuration Recommandée

**Instance PostgreSQL Managée :**
- **Type :** DB-GP-M (4 vCPU, 8GB RAM, 100GB SSD)
- **Version :** PostgreSQL 15
- **Région :** fr-par-1 (Paris) ou nl-ams-1 (Amsterdam)
- **Backup :** Automatique quotidien (rétention 7 jours)
- **High Availability :** Oui (recommandé pour production)

### 💰 Coût Estimé

| Composant | Configuration | Coût Mensuel |
|:----------|:--------------|:-------------|
| PostgreSQL DB-GP-M | 4 vCPU, 8GB RAM, 100GB | ~45€/mois |
| Backup Storage | 100GB × 7 jours | ~7€/mois |
| **Total** | | **~52€/mois** |

### 🔧 Commandes Terraform

```hcl
# scaleway_infrastructure/terraform/database.tf

resource "scaleway_rdb_instance" "rubi_studio_trading_db" {
  name              = "rubi-studio-trading-db"
  node_type         = "DB-GP-M"
  engine            = "PostgreSQL-15"
  is_ha_cluster     = true
  disable_backup    = false
  backup_schedule_frequency = 24  # Backup quotidien
  backup_schedule_retention = 7   # Rétention 7 jours
  
  user_name = "rubi_admin"
  password  = var.db_password
  
  tags = ["rubi-studio", "trading", "production"]
}

resource "scaleway_rdb_database" "trading_db" {
  instance_id = scaleway_rdb_instance.rubi_studio_trading_db.id
  name        = "rubi_trading"
}

# Outputs
output "database_endpoint" {
  value = scaleway_rdb_instance.rubi_studio_trading_db.endpoint_ip
}

output "database_port" {
  value = scaleway_rdb_instance.rubi_studio_trading_db.endpoint_port
}
```

### 🚀 Déploiement

```bash
# 1. Initialiser Terraform
cd scaleway_infrastructure/terraform
terraform init

# 2. Planifier
terraform plan -var="db_password=YOUR_SECURE_PASSWORD"

# 3. Appliquer
terraform apply -var="db_password=YOUR_SECURE_PASSWORD"

# 4. Récupérer les informations de connexion
terraform output database_endpoint
terraform output database_port
```

---

## 3. Schéma SQL Complet

### 📄 Fichier : `schema.sql`

```sql
-- ============================================================================
-- RUBI STUDIO TRADING DATABASE SCHEMA
-- Version: 3.0.0
-- PostgreSQL 15
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- ============================================================================
-- TRADING STRATEGIES TABLE
-- ============================================================================

CREATE TABLE trading_strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    symbols JSONB DEFAULT '[]'::jsonb,
    timeframes JSONB DEFAULT '["H1"]'::jsonb,
    max_positions INTEGER DEFAULT 5,
    risk_per_trade DECIMAL(5,4) DEFAULT 0.0200,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_profit DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_user_id ON trading_strategies(user_id);
CREATE INDEX idx_strategies_is_active ON trading_strategies(is_active);

-- ============================================================================
-- MT5 SESSIONS TABLE
-- ============================================================================

CREATE TABLE mt5_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    account_number VARCHAR(50) NOT NULL,
    broker VARCHAR(100) NOT NULL,
    server VARCHAR(100),
    balance DECIMAL(15,2) DEFAULT 0.00,
    equity DECIMAL(15,2) DEFAULT 0.00,
    margin DECIMAL(15,2) DEFAULT 0.00,
    margin_free DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_ping TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    disconnected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mt5_sessions_user_id ON mt5_sessions(user_id);
CREATE INDEX idx_mt5_sessions_session_id ON mt5_sessions(session_id);
CREATE INDEX idx_mt5_sessions_is_active ON mt5_sessions(is_active);
CREATE INDEX idx_mt5_sessions_account_number ON mt5_sessions(account_number);

-- ============================================================================
-- TRADING SIGNALS TABLE
-- ============================================================================

CREATE TYPE signal_type_enum AS ENUM ('BUY', 'SELL', 'CLOSE_BUY', 'CLOSE_SELL');
CREATE TYPE signal_status_enum AS ENUM ('PENDING', 'EXECUTED', 'REJECTED', 'EXPIRED');

CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trading_strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    signal_type signal_type_enum NOT NULL,
    status signal_status_enum DEFAULT 'PENDING',
    entry_price DECIMAL(15,5),
    stop_loss DECIMAL(15,5),
    take_profit DECIMAL(15,5),
    volume DECIMAL(10,2) NOT NULL,
    timeframe VARCHAR(10) DEFAULT 'H1',
    confidence DECIMAL(3,2) DEFAULT 0.50,
    indicators JSONB DEFAULT '{}'::jsonb,
    signal_time TIMESTAMP NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    status_message TEXT
);

CREATE INDEX idx_signals_user_id ON trading_signals(user_id);
CREATE INDEX idx_signals_strategy_id ON trading_signals(strategy_id);
CREATE INDEX idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX idx_signals_status ON trading_signals(status);
CREATE INDEX idx_signals_signal_time ON trading_signals(signal_time DESC);
CREATE INDEX idx_signals_received_at ON trading_signals(received_at DESC);

-- ============================================================================
-- TRADING ORDERS TABLE
-- ============================================================================

CREATE TABLE trading_orders (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER UNIQUE REFERENCES trading_signals(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mt5_order_id VARCHAR(50) UNIQUE,
    mt5_position_id VARCHAR(50),
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL,
    volume DECIMAL(10,2) NOT NULL,
    open_price DECIMAL(15,5),
    close_price DECIMAL(15,5),
    stop_loss DECIMAL(15,5),
    take_profit DECIMAL(15,5),
    profit DECIMAL(15,2) DEFAULT 0.00,
    commission DECIMAL(15,2) DEFAULT 0.00,
    swap DECIMAL(15,2) DEFAULT 0.00,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE INDEX idx_orders_user_id ON trading_orders(user_id);
CREATE INDEX idx_orders_signal_id ON trading_orders(signal_id);
CREATE INDEX idx_orders_mt5_order_id ON trading_orders(mt5_order_id);
CREATE INDEX idx_orders_symbol ON trading_orders(symbol);
CREATE INDEX idx_orders_opened_at ON trading_orders(opened_at DESC);
CREATE INDEX idx_orders_closed_at ON trading_orders(closed_at DESC);

-- ============================================================================
-- TRADING POSITIONS TABLE (positions ouvertes en temps réel)
-- ============================================================================

CREATE TABLE trading_positions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES mt5_sessions(session_id) ON DELETE CASCADE,
    ticket VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL,
    volume DECIMAL(10,2) NOT NULL,
    open_price DECIMAL(15,5) NOT NULL,
    current_price DECIMAL(15,5) NOT NULL,
    sl DECIMAL(15,5),
    tp DECIMAL(15,5),
    profit DECIMAL(15,2) DEFAULT 0.00,
    swap DECIMAL(15,2) DEFAULT 0.00,
    commission DECIMAL(15,2) DEFAULT 0.00,
    open_time TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_session_id ON trading_positions(session_id);
CREATE INDEX idx_positions_ticket ON trading_positions(ticket);
CREATE INDEX idx_positions_symbol ON trading_positions(symbol);
CREATE INDEX idx_positions_updated_at ON trading_positions(updated_at DESC);

-- ============================================================================
-- ACCOUNT SNAPSHOTS TABLE (historique des soldes)
-- ============================================================================

CREATE TABLE account_snapshots (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES mt5_sessions(session_id) ON DELETE CASCADE,
    balance DECIMAL(15,2) NOT NULL,
    equity DECIMAL(15,2) NOT NULL,
    margin DECIMAL(15,2) DEFAULT 0.00,
    margin_free DECIMAL(15,2) DEFAULT 0.00,
    margin_level DECIMAL(10,2) DEFAULT 0.00,
    profit DECIMAL(15,2) DEFAULT 0.00,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_snapshots_session_id ON account_snapshots(session_id);
CREATE INDEX idx_snapshots_timestamp ON account_snapshots(timestamp DESC);

-- Convertir en hypertable TimescaleDB pour optimiser les séries temporelles
SELECT create_hypertable('account_snapshots', 'timestamp', if_not_exists => TRUE);

-- ============================================================================
-- MARKET DATA TABLE (données de marché pour backtesting)
-- ============================================================================

CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(15,5) NOT NULL,
    high DECIMAL(15,5) NOT NULL,
    low DECIMAL(15,5) NOT NULL,
    close DECIMAL(15,5) NOT NULL,
    volume BIGINT DEFAULT 0,
    UNIQUE(symbol, timeframe, timestamp)
);

CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timeframe ON market_data(timeframe);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);

-- Convertir en hypertable TimescaleDB
SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE);

-- ============================================================================
-- PERFORMANCE METRICS TABLE
-- ============================================================================

CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trading_strategies(id) ON DELETE SET NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_profit DECIMAL(15,2) DEFAULT 0.00,
    average_profit DECIMAL(15,2) DEFAULT 0.00,
    max_profit DECIMAL(15,2) DEFAULT 0.00,
    max_loss DECIMAL(15,2) DEFAULT 0.00,
    max_drawdown DECIMAL(15,2) DEFAULT 0.00,
    sharpe_ratio DECIMAL(10,4),
    profit_factor DECIMAL(10,4),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_user_id ON performance_metrics(user_id);
CREATE INDEX idx_metrics_strategy_id ON performance_metrics(strategy_id);
CREATE INDEX idx_metrics_period_start ON performance_metrics(period_start DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON trading_strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON mt5_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON trading_positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Vue pour les statistiques de trading par utilisateur
CREATE VIEW user_trading_stats AS
SELECT 
    u.id AS user_id,
    u.username,
    COUNT(DISTINCT ts.id) AS total_strategies,
    COUNT(DISTINCT sig.id) AS total_signals,
    COUNT(DISTINCT CASE WHEN sig.status = 'EXECUTED' THEN sig.id END) AS executed_signals,
    COUNT(DISTINCT ord.id) AS total_orders,
    COUNT(DISTINCT CASE WHEN ord.closed_at IS NULL THEN ord.id END) AS open_orders,
    COALESCE(SUM(ord.profit), 0) AS total_profit,
    COALESCE(AVG(ord.profit), 0) AS average_profit
FROM users u
LEFT JOIN trading_strategies ts ON u.id = ts.user_id
LEFT JOIN trading_signals sig ON u.id = sig.user_id
LEFT JOIN trading_orders ord ON u.id = ord.user_id
GROUP BY u.id, u.username;

-- Vue pour les positions ouvertes avec informations de session
CREATE VIEW open_positions_with_session AS
SELECT 
    p.*,
    s.account_number,
    s.broker,
    s.user_id
FROM trading_positions p
JOIN mt5_sessions s ON p.session_id = s.session_id
WHERE s.is_active = TRUE;

-- ============================================================================
-- DONNÉES INITIALES
-- ============================================================================

-- Créer un utilisateur admin par défaut (mot de passe: admin123)
INSERT INTO users (email, username, hashed_password, is_superuser)
VALUES (
    'admin@rubi-studio.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJhKwHim.',  -- bcrypt hash de "admin123"
    TRUE
);

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Créer un utilisateur applicatif
CREATE USER rubi_app WITH PASSWORD 'CHANGE_ME_IN_PRODUCTION';

-- Accorder les permissions
GRANT CONNECT ON DATABASE rubi_trading TO rubi_app;
GRANT USAGE ON SCHEMA public TO rubi_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rubi_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rubi_app;

-- Permissions par défaut pour les nouvelles tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rubi_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO rubi_app;

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE users IS 'Utilisateurs de la plateforme Rubi Studio';
COMMENT ON TABLE trading_strategies IS 'Stratégies de trading configurées par les utilisateurs';
COMMENT ON TABLE mt5_sessions IS 'Sessions de connexion MT5 actives et historiques';
COMMENT ON TABLE trading_signals IS 'Signaux de trading reçus depuis MT5 ou générés par les stratégies';
COMMENT ON TABLE trading_orders IS 'Ordres de trading exécutés';
COMMENT ON TABLE trading_positions IS 'Positions ouvertes en temps réel';
COMMENT ON TABLE account_snapshots IS 'Snapshots périodiques des soldes de compte (TimescaleDB)';
COMMENT ON TABLE market_data IS 'Données de marché historiques pour backtesting (TimescaleDB)';
COMMENT ON TABLE performance_metrics IS 'Métriques de performance calculées périodiquement';

-- ============================================================================
-- FIN DU SCHÉMA
-- ============================================================================
```

---

## 4. Configuration PostgreSQL

### 📄 Fichier : `postgresql.conf` (optimisations)

```ini
# Rubi Studio Trading Database Configuration
# PostgreSQL 15

# ============================================================================
# CONNEXIONS
# ============================================================================
max_connections = 200
superuser_reserved_connections = 3

# ============================================================================
# MÉMOIRE
# ============================================================================
shared_buffers = 2GB                    # 25% de la RAM (8GB)
effective_cache_size = 6GB              # 75% de la RAM
work_mem = 16MB
maintenance_work_mem = 512MB
wal_buffers = 16MB

# ============================================================================
# CHECKPOINTS
# ============================================================================
checkpoint_completion_target = 0.9
wal_level = replica
max_wal_size = 2GB
min_wal_size = 1GB

# ============================================================================
# QUERY PLANNER
# ============================================================================
random_page_cost = 1.1                  # SSD
effective_io_concurrency = 200          # SSD

# ============================================================================
# LOGGING
# ============================================================================
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000       # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# ============================================================================
# AUTOVACUUM
# ============================================================================
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 30s

# ============================================================================
# TIMESCALEDB
# ============================================================================
shared_preload_libraries = 'timescaledb'
timescaledb.max_background_workers = 8
```

---

## 5. Extensions PostgreSQL

### 📦 Extensions Requises

```sql
-- UUID pour les session_id
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TimescaleDB pour les séries temporelles
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Statistiques de requêtes
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Full-text search (optionnel)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Chiffrement (optionnel)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

---

## 6. Indexes et Optimisations

### 🚀 Indexes Supplémentaires pour Performance

```sql
-- Index composites pour les requêtes fréquentes
CREATE INDEX idx_signals_user_status_time ON trading_signals(user_id, status, signal_time DESC);
CREATE INDEX idx_orders_user_symbol_opened ON trading_orders(user_id, symbol, opened_at DESC);
CREATE INDEX idx_positions_session_symbol ON trading_positions(session_id, symbol);

-- Index partiels pour les données actives
CREATE INDEX idx_active_sessions ON mt5_sessions(user_id, last_ping DESC) WHERE is_active = TRUE;
CREATE INDEX idx_pending_signals ON trading_signals(user_id, received_at DESC) WHERE status = 'PENDING';
CREATE INDEX idx_open_orders ON trading_orders(user_id, opened_at DESC) WHERE closed_at IS NULL;

-- Index GIN pour recherche JSON
CREATE INDEX idx_signals_indicators_gin ON trading_signals USING GIN (indicators);
CREATE INDEX idx_strategies_symbols_gin ON trading_strategies USING GIN (symbols);
```

---

## 7. Backups et Réplication

### 💾 Stratégie de Backup

**Backups Automatiques Scaleway :**
- Fréquence : Quotidien à 2h00 du matin
- Rétention : 7 jours
- Type : Snapshot complet

**Backups Manuels Supplémentaires :**

```bash
#!/bin/bash
# backup_database.sh

DB_NAME="rubi_trading"
DB_USER="rubi_admin"
DB_HOST="your-db-endpoint.scw.cloud"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup complet
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f $BACKUP_DIR/rubi_trading_$DATE.dump

# Backup SQL
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F p -f $BACKUP_DIR/rubi_trading_$DATE.sql

# Compresser
gzip $BACKUP_DIR/rubi_trading_$DATE.sql

# Uploader vers S3
aws s3 cp $BACKUP_DIR/rubi_trading_$DATE.dump s3://rubi-studio-backups/database/
aws s3 cp $BACKUP_DIR/rubi_trading_$DATE.sql.gz s3://rubi-studio-backups/database/

# Nettoyer les backups locaux > 3 jours
find $BACKUP_DIR -name "rubi_trading_*.dump" -mtime +3 -delete
find $BACKUP_DIR -name "rubi_trading_*.sql.gz" -mtime +3 -delete

echo "Backup completed: $DATE"
```

**Cron Job :**
```bash
# Backup quotidien à 3h00
0 3 * * * /opt/scripts/backup_database.sh >> /var/log/backup.log 2>&1
```

---

## 8. Monitoring et Maintenance

### 📊 Requêtes de Monitoring

```sql
-- Taille de la base de données
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'rubi_trading';

-- Taille des tables
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- Requêtes lentes
SELECT 
    calls,
    mean_exec_time,
    max_exec_time,
    query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Connexions actives
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'rubi_trading';

-- Index non utilisés
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND schemaname = 'public';
```

---

## 9. Migration depuis SQLite

### 🔄 Script de Migration

```python
# migrate_sqlite_to_postgres.py

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SQLITE_DB = "rubi_studio.db"
POSTGRES_CONFIG = {
    "host": "your-db-endpoint.scw.cloud",
    "port": 5432,
    "database": "rubi_trading",
    "user": "rubi_admin",
    "password": "YOUR_PASSWORD"
}

def migrate_table(sqlite_conn, postgres_conn, table_name, columns):
    """Migrer une table de SQLite vers PostgreSQL"""
    logger.info(f"Migrating table: {table_name}")
    
    # Lire depuis SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT {','.join(columns)} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        logger.info(f"No data in {table_name}")
        return
    
    # Insérer dans PostgreSQL
    postgres_cursor = postgres_conn.cursor()
    insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES %s"
    
    execute_values(postgres_cursor, insert_query, rows)
    postgres_conn.commit()
    
    logger.info(f"Migrated {len(rows)} rows to {table_name}")

def main():
    # Connexions
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
    
    try:
        # Migrer les tables
        migrate_table(
            sqlite_conn, postgres_conn,
            "users",
            ["email", "username", "hashed_password", "is_active", "created_at"]
        )
        
        migrate_table(
            sqlite_conn, postgres_conn,
            "trading_strategies",
            ["user_id", "name", "description", "symbols", "timeframes", "max_positions", "risk_per_trade"]
        )
        
        migrate_table(
            sqlite_conn, postgres_conn,
            "trading_signals",
            ["user_id", "strategy_id", "symbol", "signal_type", "status", "entry_price", "stop_loss", "take_profit", "volume", "signal_time", "received_at"]
        )
        
        # ... autres tables
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        postgres_conn.rollback()
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    main()
```

---

## 10. Scripts d'Installation

### 🚀 Installation Complète

```bash
#!/bin/bash
# install_database.sh

set -e

echo "🚀 Installation de la base de données Rubi Studio Trading..."

# Variables
DB_HOST="your-db-endpoint.scw.cloud"
DB_PORT=5432
DB_NAME="rubi_trading"
DB_USER="rubi_admin"
DB_PASSWORD="$1"

if [ -z "$DB_PASSWORD" ]; then
    echo "Usage: ./install_database.sh <db_password>"
    exit 1
fi

# 1. Tester la connexion
echo "📡 Test de connexion..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT version();"

# 2. Créer la base de données
echo "📦 Création de la base de données..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

# 3. Installer les extensions
echo "🔧 Installation des extensions..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME <<EOF
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOF

# 4. Exécuter le schéma
echo "📄 Exécution du schéma SQL..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f schema.sql

# 5. Vérifier les tables
echo "✅ Vérification des tables..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt"

echo "✅ Installation terminée avec succès!"
echo ""
echo "📝 Informations de connexion:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo "🔐 Chaîne de connexion:"
echo "  postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"
```

---

## 📊 Résumé

### ✅ Checklist d'Installation

- [ ] Provisionner PostgreSQL sur Scaleway (DB-GP-M)
- [ ] Configurer les backups automatiques
- [ ] Installer les extensions (uuid-ossp, timescaledb, pg_stat_statements)
- [ ] Exécuter le schéma SQL complet
- [ ] Créer les indexes et optimisations
- [ ] Configurer les triggers
- [ ] Créer les vues
- [ ] Insérer les données initiales
- [ ] Configurer les permissions
- [ ] Tester la connexion depuis l'API
- [ ] Configurer les backups manuels
- [ ] Mettre en place le monitoring
- [ ] Migrer les données depuis SQLite (si applicable)

### 📈 Performance Attendue

- **Connexions simultanées :** 200
- **Requêtes par seconde :** 1000+
- **Latence moyenne :** < 10ms
- **Stockage :** 100GB (extensible)
- **Backup :** Quotidien automatique
- **High Availability :** Oui

### 💰 Coût Total

**~52€/mois** pour une base de données production-ready avec haute disponibilité et backups automatiques.

---

**Auteur :** Expert Architecte Senior Backend  
**Date :** 23 Octobre 2025  
**Version :** 3.0.0

