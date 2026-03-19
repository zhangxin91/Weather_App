// Configuration
const API_BASE_URL = 'http://localhost:5000';
const API_KEY = 'key_test_123';

// État de l'application
let currentWeatherMode = 'city';
let currentUnits = 'metric';

// ==================== INITIALISATION ====================

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadInitialWeather();
});

function setupEventListeners() {
    // Tabs
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', switchTab);
    });

    // Buttons
    document.getElementById('current-weather-btn').addEventListener('click', getCurrentWeather);
    document.getElementById('forecast-btn').addEventListener('click', getForecast);
    document.getElementById('use-location-btn').addEventListener('click', useMyLocation);

    // Selects
    document.getElementById('units-select').addEventListener('change', (e) => {
        currentUnits = e.target.value;
    });

    document.getElementById('days-select').addEventListener('change', (e) => {
        const days = parseInt(e.target.value, 10);  // ← Convertir !
        getForecast(days);
    });

    // Enter key
    document.getElementById('city-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') getCurrentWeather();
    });

    setupCitySuggestions();
}

// Liste des villes populaires
const POPULAR_CITIES = [
    'Paris', 'Londres', 'Tokyo', 'New York', 'Berlin',
    'Madrid', 'Rome', 'Amsterdam', 'Barcelone', 'Lisbonne',
    'Montréal', 'Sydney', 'Bangkok', 'Singapour', 'Dubaï',
    'Istanbul', 'Athènes', 'Prague', 'Vienne', 'Bruxelles',
    'Zurich', 'Genève', 'Stockholm', 'Copenhague', 'Oslo',
    'Hong Kong', 'Shanghai', 'Pékin', 'Delhi', 'Mumbai',
    'Bali', 'Cancun', 'Miami', 'Los Angeles', 'San Francisco',
    'Toronto', 'Mexico City', 'São Paulo', 'Buenos Aires', 'Santiago'
];

// ==================== CITY SUGGESTIONS ====================

let ALL_CITIES = [];

// ==================== CHARGER LES VILLES AU DÉMARRAGE ====================

async function loadCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/cities`);
        const data = await response.json();
        
        if (data.status === 'success') {
            ALL_CITIES = data.data;
            console.log(`✅ ${ALL_CITIES.length} villes chargées`);
        }
    } catch (error) {
        console.error('Erreur lors du chargement des villes:', error);
    }
}

// ==================== CITY SUGGESTIONS ====================

function setupCitySuggestions() {
    const cityInput = document.getElementById('city-input');
    const suggestionsList = document.getElementById('city-suggestions');

    // Au clic sur le champ, afficher TOUTES les villes
    cityInput.addEventListener('focus', (e) => {
        displayAllCities(ALL_CITIES);
    });

    // En tapant, filtrer les villes
    cityInput.addEventListener('input', (e) => {
        const value = e.target.value.trim().toLowerCase();

        if (value.length === 0) {
            // Si vide, afficher toutes les villes
            displayAllCities(ALL_CITIES);
            return;
        }

        // Filtrer les villes selon le texte
        const filtered = ALL_CITIES.filter(city =>
            city.toLowerCase().includes(value)
        );

        if (filtered.length === 0) {
            suggestionsList.classList.add('hidden');
            return;
        }

        displayCities(filtered);
    });

    // Fermer les suggestions quand on clique ailleurs
    document.addEventListener('click', (e) => {
        if (e.target.id !== 'city-input') {
            suggestionsList.classList.add('hidden');
        }
    });
}

function displayAllCities(cities) {
    const suggestionsList = document.getElementById('city-suggestions');
    
    // Afficher max 20 villes à la fois (avec scroll)
    const displayCities = cities.slice(0, 20);
    
    suggestionsList.innerHTML = displayCities.map(city => `
        <li class="city-suggestion-item" onclick="selectCity('${city}')">
            🏙️ ${city}
        </li>
    `).join('');

    suggestionsList.classList.remove('hidden');
}

function displayCities(cities) {
    const suggestionsList = document.getElementById('city-suggestions');
    
    // Afficher max 15 résultats filtrés
    const displayCities = cities.slice(0, 15);
    
    suggestionsList.innerHTML = displayCities.map(city => `
        <li class="city-suggestion-item" onclick="selectCity('${city}')">
            🏙️ ${city}
        </li>
    `).join('');

    suggestionsList.classList.remove('hidden');
}

function selectCity(city) {
    document.getElementById('city-input').value = city;
    document.getElementById('city-suggestions').classList.add('hidden');
}

function selectCity(city) {
    document.getElementById('city-input').value = city;
    document.getElementById('city-suggestions').classList.add('hidden');
}

// ==================== TAB SWITCHING ====================

function switchTab(e) {
    const tabName = e.target.dataset.tab;

    // Remove active class from all tabs
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // Add active class to clicked tab
    e.target.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');

    currentWeatherMode = tabName;
}

// ==================== GET WEATHER DATA ====================

async function getCurrentWeather() {
    let url = `${API_BASE_URL}/weather/current`;
    let params = {};

    if (currentWeatherMode === 'city') {
        const city = document.getElementById('city-input').value.trim();
        if (!city) {
            showError('Veuillez entrer un nom de ville');
            return;
        }
        params.city = city;
    } else {
        const lat = document.getElementById('lat-input').value;
        const lon = document.getElementById('lon-input').value;
        if (!lat || !lon) {
            showError('Veuillez entrer les coordonnées GPS');
            return;
        }
        params.lat = parseFloat(lat);  // ← Convertir !
        params.lon = parseFloat(lon);  // ← Convertir !
    }

    params.units = currentUnits;

    await fetchWeatherData(url, params, displayCurrentWeather);
}

async function getForecast(daysParam = null) {
    let days;
    
    // Si un paramètre est passé ET valide, l'utiliser
    if (daysParam !== null && daysParam !== undefined && !isNaN(daysParam)) {
        days = parseInt(daysParam, 10);
    } else {
        // Sinon, lire depuis le sélecteur
        const daysValue = document.getElementById('days-select').value;
        console.log('Days value from select:', daysValue); // DEBUG
        days = parseInt(daysValue, 10);
    }
    
    console.log('Nombre de jours final:', days); // DEBUG
    
    // Vérifier que days est un nombre valide
    if (isNaN(days) || days < 1 || days > 7) {
        console.error('Days invalide:', days); // DEBUG
        showError('Nombre de jours invalide (1-7)');
        return;
    }

    let url = `${API_BASE_URL}/weather/forecast`;
    let params = { days: days };

    if (currentWeatherMode === 'city') {
        const city = document.getElementById('city-input').value.trim();
        if (!city) {
            showError('Veuillez entrer un nom de ville');
            return;
        }
        params.city = city;
    } else {
        const lat = document.getElementById('lat-input').value;
        const lon = document.getElementById('lon-input').value;
        if (!lat || !lon) {
            showError('Veuillez entrer les coordonnées GPS');
            return;
        }
        params.lat = parseFloat(lat);
        params.lon = parseFloat(lon);
    }

    params.units = currentUnits;

    console.log('Requête Forecast:', params);  // DEBUG
    await fetchWeatherData(url, params, displayForecast);
}
async function fetchWeatherData(url, params, callback) {
    showLoading(true);

    try {
        // Construire l'URL avec les paramètres
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = `${url}?${queryString}`;

        const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error?.message || 'Erreur API');
        }

        if (data.status === 'success') {
            callback(data.data);
        } else {
            showError(data.error?.message || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Erreur lors du chargement des données');
    } finally {
        showLoading(false);
    }
}

// ==================== DISPLAY FUNCTIONS ====================

function displayCurrentWeather(data) {
    const section = document.getElementById('current-weather-section');
    const content = document.getElementById('current-weather-content');

    const location = data.location;
    const current = data.current;

    const tempUnit = currentUnits === 'metric' ? '°C' : '°F';
    const windUnit = currentUnits === 'metric' ? 'm/s' : 'mph';

    content.innerHTML = `
        <div class="weather-location">
            <h3>${location.city}</h3>
            <div class="location-info">
                <p>${location.country} • Latitude: ${location.coordinates.latitude.toFixed(2)} • Longitude: ${location.coordinates.longitude.toFixed(2)}</p>
            </div>
        </div>

        <div class="weather-main">
            <div class="description">${current.description}</div>
            <div class="temperature">${current.temperature.toFixed(1)}${tempUnit}</div>
            <div class="weather-details">
                <div class="detail-item">
                    <div class="detail-icon">💧</div>
                    <div class="detail-value">${current.humidity}%</div>
                    <div class="detail-label">Humidité</div>
                </div>
                <div class="detail-item">
                    <div class="detail-icon">💨</div>
                    <div class="detail-value">${current.wind_speed.toFixed(1)}</div>
                    <div class="detail-label">Vent (${windUnit})</div>
                </div>
                <div class="detail-item">
                    <div class="detail-icon">☁️</div>
                    <div class="detail-value">${current.cloudiness}%</div>
                    <div class="detail-label">Nuages</div>
                </div>
                <div class="detail-item">
                    <div class="detail-icon">🌡️</div>
                    <div class="detail-value">${current.temperature.toFixed(1)}${tempUnit}</div>
                    <div class="detail-label">Température</div>
                </div>
            </div>
        </div>
    `;

    section.classList.remove('hidden');
    document.getElementById('forecast-section').classList.add('hidden');
}

function displayForecast(data) {
    const section = document.getElementById('forecast-section');
    const content = document.getElementById('forecast-content');

    const tempUnit = currentUnits === 'metric' ? '°C' : '°F';

    let forecastHTML = '';

    data.forecasts.forEach(day => {
        const date = new Date(day.date).toLocaleDateString('fr-FR', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });

        forecastHTML += `
            <div class="forecast-day">
                <div class="forecast-date">${date}</div>
                <div class="forecast-temp">
                    ${day.day.temperature_max.toFixed(1)}${tempUnit} / ${day.day.temperature_min.toFixed(1)}${tempUnit}
                </div>
                <div class="forecast-description">${day.day.description}</div>
                <div class="forecast-details">
                    <p>💧 Humidité: ${day.day.humidity}%</p>
                    <p>🌧️ Pluie: ${day.day.rain_probability}%</p>
                    <p>💨 Vent: ${day.day.wind_speed.toFixed(1)} km/h</p>
                    <p>📊 Moyenne: ${day.day.temperature_avg.toFixed(1)}${tempUnit}</p>
                </div>
            </div>
        `;
    });

    content.innerHTML = forecastHTML;
    section.classList.remove('hidden');
    document.getElementById('current-weather-section').classList.add('hidden');
}

// ==================== GÉOLOCALISATION ====================

function useMyLocation() {
    if (!navigator.geolocation) {
        showError('La géolocalisation n\'est pas supportée par votre navigateur');
        return;
    }

    showLoading(true);

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            document.getElementById('lat-input').value = latitude.toFixed(4);
            document.getElementById('lon-input').value = longitude.toFixed(4);
            showLoading(false);
            showError('Position obtenue ! Cliquez sur "Météo Actuelle" pour charger les données');
        },
        (error) => {
            showLoading(false);
            showError('Erreur de géolocalisation: ' + error.message);
        }
    );
}

// ==================== UTILITAIRES ====================

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

function showError(message) {
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    error.classList.remove('hidden');

    setTimeout(() => {
        error.classList.add('hidden');
    }, 5000);
}

function closeError() {
    document.getElementById('error').classList.add('hidden');
}

async function loadInitialWeather() {
    // Charger les villes
    await loadCities();
    
    // Charger la météo de Paris par défaut
    await getCurrentWeather();
}