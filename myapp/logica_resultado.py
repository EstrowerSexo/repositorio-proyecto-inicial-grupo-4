# logica_resultado.py

# ==============================================================================
# IMPORTACIONES CLAVE para este módulo
# ==============================================================================
import requests
import json
from datetime import date, timedelta
from calendar import monthrange
from django.http import JsonResponse, Http404 
from django.views.decorators.csrf import csrf_exempt 

# Mapeos necesarios de views.py
from .views import REGION_COORDS, REGION_BACKGROUNDS, REGIONES_CHOICES 

# Variables globales/constantes
today = date.today()

# ==============================================================================
# FUNCIÓN AUXILIAR: Cálculo de Métricas
# ==============================================================================
def calculate_metrics(daily_data):
    """
    Calcula todas las métricas clave de un conjunto de datos diarios.
    """
    times = daily_data.get('time', [])
    temps_max = daily_data.get('temperature_2m_max', [])
    temps_min = daily_data.get('temperature_2m_min', [])
    precips = daily_data.get('precipitation_sum', [])
    wind_speeds = daily_data.get('wind_speed_10m_max', [])
    radiation = daily_data.get('shortwave_radiation_sum', [])
    humidity_max = daily_data.get('relative_humidity_2m_max', [])   
    num_days = len(times)
    
    if num_days == 0:
        return None 
    
    # Cálculo de métricas
    temp_max_avg = round(sum(temps_max) / num_days, 1) if temps_max else 0.0
    temp_min_avg = round(sum(temps_min) / num_days, 1) if temps_min else 0.0
    precip_sum = round(sum(precips), 1) if precips else 0.0
    wind_max = round(max(wind_speeds), 1) if wind_speeds else 0.0
    radiation_sum = round(sum(radiation), 1) if radiation else 0.0
    humidity_max_abs = round(max(humidity_max), 0) if humidity_max else 0.0

    return {
        'num_dias': num_days,
        'temp_max_avg': temp_max_avg, 
        'temp_min_avg': temp_min_avg, 
        'precip_sum': precip_sum,
        'wind_max': wind_max,
        'radiation_sum': radiation_sum,
        'temp_max_abs': round(max(temps_max), 1) if temps_max else 0.0,
        'temp_min_abs': round(min(temps_min), 1) if temps_min else 0.0,
        'humidity_max_abs': humidity_max_abs,
    }

# ==============================================================================
# VISTA AJAX: fetch_clima_data_ajax - Histórico
# ==============================================================================
@csrf_exempt 
def fetch_clima_data_ajax(request):
    """
    Maneja la solicitud AJAX para Histórico Anual/Mensual (API ARCHIVE).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    # 1. Obtener parámetros clave
    region_code = data.get('region_code')
    year = int(data.get('year'))
    month = int(data.get('month'))
    is_forecast = data.get('is_forecast', False) 
    period_end_limit = data.get('period_end')    

    if not region_code:
        return JsonResponse({'error': 'Falta el código de la región'}, status=400)
    
    lat, lon = REGION_COORDS.get(region_code)

    if is_forecast:
        return JsonResponse({'success': False, 'message': 'El pronóstico se maneja en una URL diferente.'}, status=400)
    
    # LÓGICA DE HISTÓRICO (Slider) - Usa la API de ARCHIVE
    API_URL = "https://archive-api.open-meteo.com/v1/archive" 

    # 2a. Definir Fechas de Inicio y Fin basadas en el mes para el ARCHIVE
    if month == 0:
        # Año completo solicitado
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        periodo_label = f"Anual ({year})"
    else:
        # Mes específico solicitado
        last_day = monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        periodo_label = start_date.strftime('%B').capitalize()

    # === Solo recortar el rango si se trata del año o mes actual ===
    if period_end_limit:
        limit_obj = date.fromisoformat(period_end_limit)

        if month == 0:
            if year == today.year and end_date > limit_obj:
                end_date = limit_obj
        else:
            if year == today.year and month == today.month and end_date > limit_obj:
                end_date = limit_obj

    # Parámetros para el Archive
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date, 
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum,relative_humidity_2m_max', 
        'timezone': 'auto'
    }

    # 3. Solicitud a la API
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status() 
        api_data = response.json()      
        
        # 4. Procesar la respuesta
        if api_data.get('daily'):
            metrics = calculate_metrics(api_data['daily'])
            
            if metrics:
                return JsonResponse({
                    'success': True,
                    'periodo_label': periodo_label,
                    'metrics': metrics,
                    'is_forecast_result': is_forecast
                })
            else:
                return JsonResponse({'success': False, 'message': 'API no devolvió datos diarios para este periodo.'}, status=404)
        else:
            return JsonResponse({'success': False, 'message': 'API no devolvió datos diarios para este periodo.'}, status=404)
            
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'success': False, 'message': f'Error API: El servidor externo devolvió un error ({response.status_code}).'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error inesperado del servidor: {e}'}, status=500)
