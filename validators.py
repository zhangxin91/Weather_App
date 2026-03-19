import re
from typing import Tuple, Dict, Any
from functools import wraps
from flask import request, jsonify
from config import Config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_api_key(f):
    """Décorateur pour valider la clé API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': {
                    'code': 401,
                    'message': 'Clé API manquante',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 401
        
        if api_key not in Config.VALID_API_KEYS:
            return jsonify({
                'error': {
                    'code': 401,
                    'message': 'Clé API invalide ou non autorisée',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_location_params(city=None, lat=None, lon=None):
    """
    Valide les paramètres de localisation
    
    Retourne:
    - dict avec 'valid': True/False et 'message' si erreur
    """
    if city:
        if not isinstance(city, str) or len(city.strip()) == 0:
            return {
                'valid': False,
                'message': 'Nom de ville invalide'
            }
        return {'valid': True}
    
    if lat and lon:
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            
            if not (-90 <= lat_float <= 90):
                return {
                    'valid': False,
                    'message': 'Latitude doit être entre -90 et 90'
                }
            
            if not (-180 <= lon_float <= 180):
                return {
                    'valid': False,
                    'message': 'Longitude doit être entre -180 et 180'
                }
            
            return {'valid': True}
        except ValueError:
            return {
                'valid': False,
                'message': 'Latitude et longitude doivent être des nombres'
            }
    
    return {
        'valid': False,
        'message': 'Fournissez soit une ville, soit latitude/longitude'
    }

def validate_weather_request(city=None, lat=None, lon=None):
    """Valide une requête météo"""
    return validate_location_params(city, lat, lon)

def validate_units(units):
    """Valide les unités"""
    if units not in Config.SUPPORTED_UNITS:
        return {
            'valid': False,
            'message': f'Unités invalides. Utilisez: {", ".join(Config.SUPPORTED_UNITS)}'
        }
    return {'valid': True}

def validate_days(days):
    """Valide le nombre de jours"""
    try:
        days_int = int(days)
        if days_int < 1 or days_int > 7:
            return {
                'valid': False,
                'message': 'Nombre de jours doit être entre 1 et 7'
            }
        return {'valid': True}
    except ValueError:
        return {
            'valid': False,
            'message': 'Nombre de jours doit être un nombre entier'
        }

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """Valide la clé API"""
    if not api_key:
        return False, "Clé API manquante"
    
    if api_key not in Config.VALID_API_KEYS:
        return False, "Clé API invalide ou non autorisée"
    
    return True, "Clé API valide"

def validate_weather_request(city: str = None, lat: str = None, lon: str = None) -> Dict[str, Any]:
    """
    Valide les paramètres de requête météo.
    """
    if not city and (not lat or not lon):
        return {
            'valid': False,
            'message': "Fournissez soit une ville, soit des coordonnées (lat + lon)"
        }
    
    if lat and lon:
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            
            if not (-90 <= lat_float <= 90):
                return {
                    'valid': False,
                    'message': "Latitude entre -90 et 90"
                }
            
            if not (-180 <= lon_float <= 180):
                return {
                    'valid': False,
                    'message': "Longitude entre -180 et 180"
                }
        except ValueError:
            return {
                'valid': False,
                'message': "Coordonnées doivent être des nombres"
            }
    
    if city and (len(city) < 1 or len(city) > 100):
        return {
            'valid': False,
            'message': "Ville entre 1 et 100 caractères"
        }
    
    return {'valid': True, 'message': 'Paramètres valides'}

def validate_units(units: str) -> bool:
    """Valide les unités"""
    return units in Config.SUPPORTED_UNITS

