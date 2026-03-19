from typing import Dict, Any

class WeatherResponse:
    """Modèle de réponse standard"""
    
    def __init__(self, status: str, data: Dict[str, Any], timestamp: str):
        self.status = status
        self.data = data
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'data': self.data,
            'timestamp': self.timestamp
        }

class ErrorResponse:
    """Modèle de réponse d'erreur"""
    
    def __init__(self, code: int, message: str, timestamp: str):
        self.code = code
        self.message = message
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'timestamp': self.timestamp
            }
        }