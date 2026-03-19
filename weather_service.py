import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from config import Config

logger = logging.getLogger(__name__)

class WeatherService:
    """Service pour récupérer et traiter les données météo"""
    
    OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5"
    WEATHERAPI_URL = "https://api.weatherapi.com/v1"
    
    def __init__(self, openweathermap_key: str, weatherapi_key: str):
        self.openweathermap_key = openweathermap_key
        self.weatherapi_key = weatherapi_key
        self.rate_limit_store = {}
        self.cache = {}
    
    def check_rate_limit(self, api_key: str) -> bool:
        """Vérifie le rate limiting"""
        if api_key not in Config.VALID_API_KEYS:
            return False
        
        if api_key not in self.rate_limit_store:
            self.rate_limit_store[api_key] = {'count': 0, 'reset_time': datetime.utcnow()}
        
        store = self.rate_limit_store[api_key]
        max_requests = Config.VALID_API_KEYS[api_key].get('rate_limit', Config.DEFAULT_RATE_LIMIT)
        
        if datetime.utcnow() - store['reset_time'] > Config.RATE_LIMIT_WINDOW:
            store['count'] = 0
            store['reset_time'] = datetime.utcnow()
        
        if store['count'] >= max_requests:
            return False
        
        store['count'] += 1
        return True
    
    def get_current_weather(self, city: Optional[str] = None, 
                           lat: Optional[float] = None, 
                           lon: Optional[float] = None,
                           units: str = 'metric') -> Optional[Dict[str, Any]]:
        """Récupère la météo actuelle"""
        try:
            cache_key = f"weather_{city}_{lat}_{lon}_{units}"
            if Config.ENABLE_CACHE and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.utcnow() - cached_data['timestamp'] < timedelta(seconds=Config.CACHE_TTL):
                    logger.info(f"Cache hit: {city or f'{lat},{lon}'}")
                    return cached_data['data']
            
            params = {
                'appid': self.openweathermap_key,
                'units': units
            }
            
            if city:
                params['q'] = city
            else:
                params['lat'] = lat
                params['lon'] = lon
            
            response = requests.get(
                f"{self.OPENWEATHERMAP_URL}/weather",
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur OpenWeatherMap: {response.status_code}")
                return None
            
            weather_data = response.json()
            
            self.cache[cache_key] = {
                'data': weather_data,
                'timestamp': datetime.utcnow()
            }
            
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur requête: {str(e)}")
            return None
    
    def get_weather_forecast(self, city: Optional[str] = None,
                            lat: Optional[float] = None,
                            lon: Optional[float] = None,
                            days: int = 3,
                            units: str = 'metric') -> Optional[Dict[str, Any]]:
        """Récupère les prévisions"""
        try:
            cache_key = f"forecast_{city}_{lat}_{lon}_{days}_{units}"
            if Config.ENABLE_CACHE and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.utcnow() - cached_data['timestamp'] < timedelta(seconds=Config.CACHE_TTL):
                    return cached_data['data']
            
            location = city if city else f"{lat},{lon}"
            
            params = {
                'key': self.weatherapi_key,
                'q': location,
                'days': days,
                'aqi': 'yes'
            }
            
            response = requests.get(
                f"{self.WEATHERAPI_URL}/forecast.json",
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur WeatherAPI: {response.status_code}")
                return None
            
            forecast_data = response.json()
            
            self.cache[cache_key] = {
                'data': forecast_data,
                'timestamp': datetime.utcnow()
            }
            
            return forecast_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur prévisions: {str(e)}")
            return None
    
    def process_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données météo"""
        try:
            processed = {
                'location': {
                    'city': raw_data.get('name'),
                    'country': raw_data.get('sys', {}).get('country'),
                    'coordinates': {
                        'latitude': raw_data.get('coord', {}).get('lat'),
                        'longitude': raw_data.get('coord', {}).get('lon')
                    }
                },
                'current': {
                    'temperature': raw_data.get('main', {}).get('temp'),
                    'humidity': raw_data.get('main', {}).get('humidity'),
                    'description': raw_data.get('weather', [{}])[0].get('description'),
                    'wind_speed': raw_data.get('wind', {}).get('speed'),
                    'cloudiness': raw_data.get('clouds', {}).get('all'),
                }
            }
            return processed
        except Exception as e:
            logger.error(f"Erreur traitement: {str(e)}")
            return raw_data
    
    def process_forecast_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite les prévisions
        """
        try:
            print(f"\n🔍 DEBUG process_forecast_data:")
            print(f"   Raw data keys: {raw_data.keys()}")
            
            # WeatherAPI utilise une structure différente
            # Structure: {'location': {...}, 'forecast': {'forecastday': [...]}, 'current': {...}}
            
            forecast_days = raw_data.get('forecast', {}).get('forecastday', [])
            location_data = raw_data.get('location', {})
            
            print(f"   Forecast days found: {len(forecast_days)}")
            
            processed_forecast = []
            
            for day in forecast_days:
                day_data = {
                    'date': day.get('date'),
                    'day': {
                        'temperature_max': day.get('day', {}).get('maxtemp_c'),
                        'temperature_min': day.get('day', {}).get('mintemp_c'),
                        'temperature_avg': day.get('day', {}).get('avgtemp_c'),
                        'humidity': day.get('day', {}).get('avghumidity'),
                        'description': day.get('day', {}).get('condition', {}).get('text'),
                        'rain_probability': day.get('day', {}).get('daily_chance_of_rain'),
                        'rain_volume': day.get('day', {}).get('totalprecip_mm'),
                        'wind_speed': day.get('day', {}).get('maxwind_kph'),
                        'cloudiness': day.get('day', {}).get('avg_vis_km')
                    },
                    'hours': []
                }
                
                # Ajouter les données horaires
                for hour in day.get('hour', []):
                    hour_data = {
                        'time': hour.get('time'),
                        'temperature': hour.get('temp_c'),
                        'humidity': hour.get('humidity'),
                        'description': hour.get('condition', {}).get('text'),
                        'rain_probability': hour.get('chance_of_rain'),
                        'wind_speed': hour.get('wind_kph')
                    }
                    day_data['hours'].append(hour_data)
                
                processed_forecast.append(day_data)
            
            result = {
                'location': {
                    'city': location_data.get('name'),
                    'country': location_data.get('country'),
                    'region': location_data.get('region'),
                    'coordinates': {
                        'latitude': location_data.get('lat'),
                        'longitude': location_data.get('lon')
                    }
                },
                'forecasts': processed_forecast
            }
            
            print(f"   ✅ Processed {len(processed_forecast)} days")
            return result
            
        except Exception as e:
            logger.error(f"Erreur traitement prévisions: {str(e)}")
            print(f"   ❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return raw_data