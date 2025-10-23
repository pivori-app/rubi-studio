from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Configuration de la base de données
# Utilise PostgreSQL en production, SQLite en développement
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./rubi_studio.db"  # Fallback pour développement
)

# Pour PostgreSQL, l'URL doit être au format:
# postgresql://user:password@host:port/database
# Exemple: postgresql://rubi:password@localhost:5432/rubi_studio

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    pool_size=10,  # Taille du pool de connexions
    max_overflow=20  # Connexions supplémentaires en cas de pic
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

