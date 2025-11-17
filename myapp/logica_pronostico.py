# logica_pronostico.py

# ==============================================================================
# IMPORTACIONES CLAVE para este módulo
# ==============================================================================
import requests
import json
from datetime import date, timedelta
from django.http import JsonResponse, Http404 
from django.views.decorators.csrf import csrf_exempt 

# Mapeos necesarios de views.py
from .views import REGION_COORDS 

# Importamos la función de cálculo de métricas de logica_resultado
from .logica_resultado import calculate_metrics 

# Variables globales/constantes
today = date.today()

# ==============================================================================
# FUNCIÓN AUXILIAR: Extracción de Temperaturas por Hora (12 PM y 6 PM)
# ==============================================================================
def extract_hourly_temps(api_data):
    """
    Busca la temperatura a las 12:00 (mediodía) y 18:00 (tarde) en los datos horarios.
    """
    hourly_data = api_data.get('hourly', {})
    hourly_time = hourly_data.get('time', [])
    hourly_temp = hourly_data.get('temperature_2m', [])
    
    if not hourly_time or not hourly_temp:
        return None

    # Las horas están en formato 'YYYY-MM-DDTHH:00'. Buscamos los índices de 12:00 y 18:00.
    temp_12pm = 0.0
    temp_6pm = 0.0
    
    found_12 = False
    found_18 = False
    
    for i, t in enumerate(hourly_time):
        if t.endswith('T12:00'):
            temp_12pm = round(hourly_temp[i], 1)
            found_12 = True 
        elif t.endswith('T18:00'):
            temp_6pm = round(hourly_temp[i], 1)
            found_18 = True
            
        if found_12 and found_18:
            break

    return {
        'temp_12pm': temp_12pm,
        'temp_6pm': temp_6pm,
    }

# ==============================================================================
# VISTA AJAX: fetch_pronostico_ajax - Diario/Forecast
# ==============================================================================
@csrf_exempt 
def fetch_pronostico_ajax(request):
    """
    Maneja la solicitud AJAX para Pronóstico diario Open-Meteo V1 y datos históricos recientes.
    El slider va de -14 a +14 días.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    region_code = data.get('region_code')
    days_offset = int(data.get('days_offset', 0)) # Offset: -14 a +14
    
    if not region_code:
        return JsonResponse({'error': 'Falta el código de la región'}, status=400)
    
    lat, lon = REGION_COORDS.get(region_code)

    # 1. Calcular la fecha de consulta
    today = date.today()
    target_date = today + timedelta(days=days_offset)
    target_date_string = target_date.strftime('%Y-%m-%d')
    
    # 2. Definir API URL y parámetros
    if days_offset < 0: # Histórico Reciente (hasta 14 días atrás)
        API_URL = "https://archive-api.open-meteo.com/v1/archive" 
        start_date = target_date_string
        end_date = target_date_string
        periodo_label = f"Histórico: {target_date_string}"
        is_forecast_result = False
    
    else: # Hoy (0) o Forecast (1 a +14)
        API_URL = "https://api.open-meteo.com/v1/forecast"
        start_date = target_date_string
        end_date = target_date_string 
        
        if days_offset == 0:
            periodo_label = f"Actualidad: {target_date_string}"
        else:
            periodo_label = f"Pronóstico: {target_date_string}"
        
        is_forecast_result = True
        
    
    # Parámetros 
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date, 
        'hourly': 'temperature_2m',
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum,relative_humidity_2m_max', 
        'timezone': 'auto'
    }

    # 3. Solicitud a la API
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status() 
        api_data = response.json()
        
        # 4. Procesar la respuesta
        hourly_metrics = extract_hourly_temps(api_data) 
        daily_metrics = calculate_metrics(api_data.get('daily', {})) # USAMOS calculate_metrics DE logica_resultado
        
        if hourly_metrics and daily_metrics:
            final_metrics = {**hourly_metrics, **daily_metrics}
            
            # 5. Devolver las métricas
            return JsonResponse({
                'success': True,
                'periodo_label': periodo_label,
                'metrics': final_metrics,
                'is_forecast_result': is_forecast_result
            })
        else:
            return JsonResponse({'success': False, 'message': 'API no devolvió datos para la fecha seleccionada.'}, status=404)
            
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'success': False, 'message': f'Error API: El servidor externo devolvió un error ({response.status_code}).'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error inesperado del servidor: {e}'}, status=500)