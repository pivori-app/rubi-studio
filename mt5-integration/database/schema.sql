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
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJhKwHim.',
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

