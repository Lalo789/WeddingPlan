import os
from datetime import timedelta

# --- CORRECCIÓN IMPORTANTE ---
# Obtenemos la URL de la variable de entorno (Render).
# Si no existe, usamos la local (Tu PC).
database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = database_url or "postgresql://postgres:12345@localhost:5432/WeddingPlan?client_encoding=latin1"

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2025'

WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

REMEMBER_COOKIE_DURATION = timedelta(days=7)
REMEMBER_COOKIE_SECURE = False
REMEMBER_COOKIE_HTTPONLY = True