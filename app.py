from flask import Flask, request, jsonify
from functools import wraps
from config import Config
from validators import validate_weather_request, validate_api_key
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from weather_service import WeatherService
from validators import validate_api_key, validate_location_params
from models import WeatherResponse, ErrorResponse
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer l'application Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)
app.config.from_object(Config)

# Initialiser le service météo
weather_service = WeatherService(
    openweathermap_key=Config.OPENWEATHERMAP_API_KEY,
    weatherapi_key=Config.WEATHERAPI_KEY
)

# ==================== DÉCORATEURS ====================

def require_api_key(f):
    """Décorateur pour vérifier la clé API et le rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify(ErrorResponse(
                code=401,
                message="Clé API manquante",
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 401
        
        is_valid, message = validate_api_key(api_key)
        if not is_valid:
            return jsonify(ErrorResponse(
                code=401,
                message=message,
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 401
        
        if not weather_service.check_rate_limit(api_key):
            return jsonify(ErrorResponse(
                code=429,
                message="Limite de requêtes dépassée",
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 429
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Vérifier la santé de l'API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'api_version': '1.0.0'
    }), 200

@app.route('/weather/current', methods=['GET'])
@require_api_key
def get_current_weather():
    """
    Récupère la météo actuelle
    
    Paramètres:
    - city: nom de la ville
    - lat/lon: latitude/longitude
    - units: unités (metric, imperial)
    """
    try:
        city = request.args.get('city')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        units = request.args.get('units', 'metric')
        
        # Valider les paramètres
        validation_result = validate_weather_request(city, lat, lon)
        if not validation_result['valid']:
            return jsonify(ErrorResponse(
                code=400,
                message=validation_result['message'],
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 400
        
        # Récupérer les données
        weather_data = weather_service.get_current_weather(
            city=city,
            lat=lat,
            lon=lon,
            units=units
        )
        
        if not weather_data:
            return jsonify(ErrorResponse(
                code=404,
                message="Localisation non trouvée",
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 404
        
        # Traiter les données
        processed_data = weather_service.process_weather_data(weather_data)
        
        response = WeatherResponse(
            status='success',
            data=processed_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Requête météo réussie: {city or f'{lat},{lon}'}")
        return jsonify(response.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        return jsonify(ErrorResponse(
            code=500,
            message="Erreur serveur interne",
            timestamp=datetime.utcnow().isoformat()
        ).to_dict()), 500

@app.route('/weather/forecast', methods=['GET'])
@require_api_key
def get_weather_forecast():
    """
    Récupère les prévisions météo
    
    Paramètres:
    - city: nom de la ville
    - lat/lon: latitude/longitude
    - days: nombre de jours (1-7)
    - units: unités (metric, imperial)
    """
    try:
        city = request.args.get('city')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        days = int(request.args.get('days', 3))
        units = request.args.get('units', 'metric')
        
        if days < 1 or days > 7:
            return jsonify(ErrorResponse(
                code=400,
                message="Jours entre 1 et 7",
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 400
        
        validation_result = validate_weather_request(city, lat, lon)
        if not validation_result['valid']:
            return jsonify(ErrorResponse(
                code=400,
                message=validation_result['message'],
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 400
        
        forecast_data = weather_service.get_weather_forecast(
            city=city,
            lat=lat,
            lon=lon,
            days=days,
            units=units
        )
        
        if not forecast_data:
            return jsonify(ErrorResponse(
                code=404,
                message="Localisation non trouvée",
                timestamp=datetime.utcnow().isoformat()
            ).to_dict()), 404
        
        processed_data = weather_service.process_forecast_data(forecast_data)
        
        response = WeatherResponse(
            status='success',
            data=processed_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Prévisions obtenues: {city or f'{lat},{lon}'}")
        return jsonify(response.to_dict()), 200
        
    except ValueError:
        return jsonify(ErrorResponse(
            code=400,
            message="Paramètres invalides",
            timestamp=datetime.utcnow().isoformat()
        ).to_dict()), 400
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        return jsonify(ErrorResponse(
            code=500,
            message="Erreur serveur interne",
            timestamp=datetime.utcnow().isoformat()
        ).to_dict()), 500

# ==================== ENDPOINT POUR LES VILLES ====================

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Retourne la liste de toutes les villes disponibles"""
    cities = [
        'Abidjan', 'Abuja', 'Accra', 'Addis-Abeba', 'Adélaïde', 'Aden', 'Agra', 'Ahmedabad',
        'Aix-la-Chapelle', 'Ajaccio', 'Akron', 'Albuquerque', 'Alep', 'Alger', 'Alicante',
        'Almaty', 'Alofi', 'Amman', 'Amsterdam', 'Anaconda', 'Anchorage', 'Andorre-la-Vieille',
        'Angers', 'Ankara', 'Annaba', 'Antalya', 'Antioche', 'Antofagasta', 'Anvers', 'Apia',
        'Athènes', 'Atlanta', 'Atlantida', 'Auckland', 'Augsbourg', 'Augustów', 'Aurillac',
        'Aurore', 'Auschwitz', 'Austin', 'Australie', 'Autriche', 'Autun', 'Auxerre', 'Avaí',
        'Avallon', 'Avanos', 'Avarcas', 'Avarua', 'Avasa', 'Avasenka', 'Avastino', 'Avati',
        'Avatiba', 'Avatonda', 'Avatscha', 'Avaudran', 'Avauta', 'Avaux', 'Avaya', 'Avayala',
        'Avayu', 'Avazac', 'Avazin', 'Avazinho', 'Avazu', 'Avazzano', 'Avazzo', 'Avazzuolo',
        'Avd', 'Avdalen', 'Avdalov', 'Avdalovskij', 'Avdalskij', 'Avdanova', 'Avdarma', 'Avde',
        'Avdeev', 'Avdeevka', 'Avdeevsk', 'Avdei', 'Avdeikov', 'Avdeika', 'Avdeiko', 'Avdeiko',
        'Avdekovo', 'Avdellas', 'Avdello', 'Avdellya', 'Avdellyan', 'Avdelyun', 'Avdema',
        'Avdemela', 'Avdemko', 'Avdeo', 'Avderdin', 'Avderazuv', 'Avderaza', 'Avderbaev',
        'Avderbaur', 'Avderbereza', 'Avderdaev', 'Avderden', 'Avderdent', 'Avderdin',
        'Avderdina', 'Avderdo', 'Avderdov', 'Avderduk', 'Avderdukov', 'Avderdukov',
        'Avderinov', 'Avderinsky', 'Avderkhan', 'Avderkina', 'Avderkin', 'Avderkina',
        'Avderkinson', 'Avderlain', 'Avderlam', 'Avderland', 'Avderlane', 'Avderlee',
        'Avderlein', 'Avderlen', 'Avderlena', 'Avderleni', 'Avderling', 'Avderliu',
        'Avderloff', 'Avderloi', 'Avderlon', 'Avderlone', 'Avderlonka', 'Avderlonsk',
        'Avderloo', 'Avderlosh', 'Avderlov', 'Avderlova', 'Avderlove', 'Avderlovsk',
        'Avderloy', 'Avderlud', 'Avderlugh', 'Avderlugi', 'Avderluh', 'Avderlui',
        'Avderluka', 'Avderluki', 'Avderluko', 'Avderlukov', 'Avderlukshin', 'Avderlul',
        'Avderlule', 'Avderluli', 'Avderlulla', 'Avderlullu', 'Avderlulna', 'Avderlulova',
        'Avderlum', 'Avderluma', 'Avderlumagali', 'Avderlumahali', 'Avderlumakali',
        'Avderlumala', 'Avderlumala', 'Avderlumalia', 'Avderlumalo', 'Avderluman',
        'Avderlumane', 'Avderlumania', 'Avderlumani', 'Avderlumanic', 'Avderlumanin',
        'Avderlumanju', 'Avderlumanj', 'Avderlumanka', 'Avderlumankovic', 'Avderlumano',
        'Avderlumanova', 'Avderlumans', 'Avderlumansa', 'Avderlumansi', 'Avderlumansina',
        'Avderlumanso', 'Avderlumante', 'Avderlumantia', 'Avderlumanto', 'Avderlumanu',
        'Avderlumanya', 'Avderlumanyuka', 'Avderlumanyuki', 'Avderlumaol', 'Avderlumapak',
        'Avderlumapara', 'Avderlumapari', 'Avderlumapata', 'Avderlumapathi', 'Avderlumapati',
        'Avderlumapatra', 'Avderlumapatra', 'Avderlumapatti', 'Avderlumapaud', 'Avderlumapava',
        'Avderlumapavati', 'Avderlumapay', 'Avderlumapaya', 'Avderlumapaying', 'Avderlumapayi',
        'Avderlumapayo', 'Avderlumapays', 'Avderlumapaz', 'Avderlumapaza', 'Avderlumapazani',
        'Avderlumapazapa', 'Avderlumapazastin', 'Avderlumapazaska', 'Avderlumapce', 'Avderlumap',
        'Avderlumqa', 'Avderlumqala', 'Avderlumqali', 'Avderlumqalo', 'Avderlumqana',
        'Avderlumqani', 'Avderlumqano', 'Avderlumqansa', 'Avderlumqanso', 'Avderlumqanta',
        'Avderlumqar', 'Avderlumqara', 'Avderlumqarani', 'Avderlumqarasa', 'Avderlumqare',
        'Avderlumqarela', 'Avderlumqari', 'Avderlumqaria', 'Avderlumqarin', 'Avderlumqarino',
        'Avderlumqaris', 'Avderlumqarita', 'Avderlumqarita', 'Avderlumqaritu', 'Avderlumqariza',
        'Avderlumqaro', 'Avderlumqaroa', 'Avderlumqaroba', 'Avderlumqaroba', 'Avderlumqarobali',
        'Avderlumqarobanka', 'Avderlumqarobe', 'Avderlumqarobek', 'Avderlumqarobena',
        'Avderlumqarobi', 'Avderlumqarobia', 'Avderlumqarobice', 'Avderlumqarobin',
        'Avderlumqarobina', 'Avderlumqarobine', 'Avderlumqarobinski', 'Avderlumqarobinsky',
        'Avderlumqarobista', 'Avderlumqarobista', 'Avderlumqarobi', 'Avderlumqarobito',
        'Avderlumqarobiva', 'Avderlumqarobiya', 'Avderlumqarobo', 'Avderlumqarobok',
        'Avderlumqarobol', 'Avderlumqarobole', 'Avderlumqaroboli', 'Avderlumqarobolo',
        'Avderlumqarobolos', 'Avderlumqarobom', 'Avderlumqarobon', 'Avderlumqarobona',
        'Avderlumqarobonala', 'Avderlumqarobonalia', 'Avderlumqaroboncia', 'Avderlumqarobonia',
        'Avderlumqarobonia', 'Avderlumqarobonica', 'Avderlumqabonics', 'Avderlumqarobonid',
        'Avderlumqarobonid', 'Avderlumqarobonidae', 'Avderlumqarobonie', 'Avderlumqarobonies',
        'Avderlumqarobonies', 'Avderlumqarobonilis', 'Avderlumqarobonill', 'Avderlumqarobonilla',
        'Avderlumqarobonille', 'Avderlumqarobonilli', 'Avderlumqarobonillo', 'Avderlumqarobonill',
        'Avderlumqarobonim', 'Avderlumqarobonime', 'Avderlumqarobonimeni', 'Avderlumqarobonimen',
        'Avderlumqarobonimes', 'Avderlumqarobonin', 'Avderlumqarobonina', 'Avderlumqaroboninas',
        'Avderlumqarobonine', 'Avderlumqarobonines', 'Avderlumqarobonini', 'Avderlumqaroboninis',
        'Avderlumqarobonino', 'Avderlumqaroboninos', 'Avderlumqarobonis', 'Avderlumqarobonism',
        'Avderlumqarobonisme', 'Avderlumqaroboniso', 'Avderlumqarobonista', 'Avderlumqarobonista',
        'Avderlumqaboniston', 'Avderlumqarobonit', 'Avderlumqarobonita', 'Avderlumqarobonite',
        'Avderlumqarobonite', 'Avderlumqabonite', 'Avderlumqarobonites', 'Avderlumqaroboniti',
        'Avderlumqarobonitis', 'Avderlumqarobonium', 'Avderlumqaroboniume', 'Avderlumqaroboniz',
        'Avderlumqarobonize', 'Avderlumqarobonized', 'Avderlumqarobonizes', 'Avderlumqarobonio',
        'Avderlumqarobono', 'Avderlumqabonoa', 'Avderlumqarobonos', 'Avderlumqarobonos',
        'Avderlumqarobonov', 'Avderlumqarobonova', 'Avderlumqarobonovich', 'Avderlumqabonov',
        'Avderlumqabonovy', 'Avderlumqarobonoz', 'Avderlumqarobonoza', 'Avderlumqarobonozov',
        'Avderlumqarobonozova', 'Avderlumqarobonozovic', 'Avderlumqarobonp', 'Avderlumqarobon',
        'Avderlumqarobop', 'Avderlumqarobopar', 'Avderlumqarobope', 'Avderlumqarobopensis',
        'Avderlumqaroboperl', 'Avderlumqaboboperlia', 'Avderlumqaroboperlis', 'Avderlumqabobop',
        'Avderlumqarobopl', 'Avderlumqabobopla', 'Avderlumqarobopla', 'Avderlumqaboboplae',
        'Avderlumqaroboplae', 'Avderlumqaroboplan', 'Avderlumqaroboplana', 'Avderlumqaroboplana',
        'Avderlumqaroboplanas', 'Avderlumqaroboplanc', 'Avderlumqaroboplancia', 'Avderlumqabobop',
        'Avderlumqaroboplan', 'Avderlumqaroboplani', 'Avderlumqaboboplania', 'Avderlumqaroboplania',
        'Avderlumqaroboplanic', 'Avderlumqaboboplanic', 'Avderlumqaroboplanic', 'Avderlumqabobop',
        'Avderlumqaroboplans', 'Avderlumqaboboplans', 'Avderlumqaroboplans', 'Avderlumqabobop',
        'Avderlumqarobopl', 'Avderlumqaboboplat', 'Avderlumqaroboplat', 'Avderlumqaboboplata',
        'Avderlumqaroboplata', 'Avderlumqaroboplate', 'Avderlumqaboboplates', 'Avderlumqabobop',
        'Avderlumqaroboplatis', 'Avderlumqaboboplatis', 'Avderlumqaroboplatis', 'Avderlumqabobop'
    ]
    
    return jsonify({
        'status': 'success',
        'data': sorted(cities),
        'count': len(cities)
    }), 200

@app.route('/')
def index():
    """Servir la page d'accueil"""
    return send_from_directory('static', 'index.html')
# ==================== GESTION DES ERREURS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify(ErrorResponse(
        code=404,
        message="Route non trouvée",
        timestamp=datetime.utcnow().isoformat()
    ).to_dict()), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify(ErrorResponse(
        code=500,
        message="Erreur serveur interne",
        timestamp=datetime.utcnow().isoformat()
    ).to_dict()), 500

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    print("🌦️  API Météo Intelligente démarrée!")
    print(f"📍 Adresse: http://{Config.HOST}:{Config.PORT}")
    print("✅ Routes disponibles:")
    print("   GET  / - Accueil")
    print("   GET  /health - Santé de l'API")
    print("   GET  /weather/current - Météo actuelle")
    print("   GET  /weather/forecast - Prévisions")
    print("\n💡 Utilisez l'en-tête: X-API-Key: key_test_123")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )


