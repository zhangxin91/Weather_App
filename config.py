import os
from datetime import timedelta

class Config:
    """Configuration de l'application météo"""
    
    # Paramètres Flask
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # ⭐ REMPLACEZ PAR VOS VRAIES CLÉS
    OPENWEATHERMAP_API_KEY = '5e874e08ed086d0619f068c21232ac97'  # ← Votre clé
    WEATHERAPI_KEY = '32231fcb70a747d0988104157261803'  # ← Votre clé
    
    # Clés API internes autorisées
    VALID_API_KEYS = {
        'key_test_123': {'name': 'Test User', 'rate_limit': 100},
        'key_prod_456': {'name': 'Production User', 'rate_limit': 1000},
    }
    
    # Rate limiting
    RATE_LIMIT_WINDOW = timedelta(hours=1)
    DEFAULT_RATE_LIMIT = 100
    
    # Cache
    CACHE_TTL = 600
    ENABLE_CACHE = True
    
    # Timeout
    REQUEST_TIMEOUT = 10
    
    # Unités
    DEFAULT_UNITS = 'metric'
    SUPPORTED_UNITS = ['metric', 'imperial', 'standard']