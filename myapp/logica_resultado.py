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


# ==============================================================================
# DATOS "HARDCODEADOS" (Pegados) DE LA REGIÓN METROPOLITANA (1950-2025)
# Se mantienen aquí para la lógica de fetch_evolucion_ajax
# (Se omite el contenido para brevedad, asumiendo que es la misma lista DATOS_METROPOLITANA)
# ==============================================================================
DATOS_METROPOLITANA = [
    { 'year': 1950, 'temp_max_avg': 21.6, 'temp_min_avg': 9.1, 'precip_sum': 216.2, 'radiation_sum': 7824.0 },
    { 'year': 1951, 'temp_max_avg': 21.6, 'temp_min_avg': 9.6, 'precip_sum': 757.9, 'radiation_sum': 7511.6 },
    # ... resto de los datos ...
    { 'year': 2025, 'temp_max_avg': 22.3, 'temp_min_avg': 10.7, 'precip_sum': 351.3, 'radiation_sum': 5807.6 }
]


# ==============================================================================
# FUNCIÓN AYUDANTE: Procesamiento de Datos Mensuales a Anuales (Para Gráficos)
# ==============================================================================
def process_monthly_data_for_charts(monthly_data):
    """
    Toma los datos mensuales de la API y los agrupa en datos anuales.
    """
    years_data = {}
    time_list = monthly_data.get('time', [])
    temp_max_means = monthly_data.get('temperature_2m_max', [])
    temp_min_means = monthly_data.get('temperature_2m_min', [])
    precips = monthly_data.get('precipitation_sum', [])
    radiation_sums = monthly_data.get('shortwave_radiation_sum', [])

    for i, time_str in enumerate(time_list):
        year = int(time_str[:4])
        if year not in years_data:
            years_data[year] = {
                'temp_max_list': [], 'temp_min_list': [], 'precip_sum_list': [],
                'radiation_sum_list': [],
            }
        
        if temp_max_means and i < len(temp_max_means) and temp_max_means[i] is not None:
            years_data[year]['temp_max_list'].append(temp_max_means[i])
        if temp_min_means and i < len(temp_min_means) and temp_min_means[i] is not None:
            years_data[year]['temp_min_list'].append(temp_min_means[i])
        if precips and i < len(precips) and precips[i] is not None:
            years_data[year]['precip_sum_list'].append(precips[i])
        if radiation_sums and i < len(radiation_sums) and radiation_sums[i] is not None:
            years_data[year]['radiation_sum_list'].append(radiation_sums[i])

    chart_data = []
    sorted_years = sorted(years_data.keys())
    
    for year in sorted_years:
        data = years_data[year]
        def avg(l): return round(sum(l) / len(l), 1) if l and len(l) > 0 else 0.0
        def sum_r(l): return round(sum(l), 1) if l else 0.0

        chart_data.append({
            'year': year,
            'temp_max_avg': avg(data['temp_max_list']),
            'temp_min_avg': avg(data['temp_min_list']),
            'precip_sum': sum_r(data['precip_sum_list']),
            'radiation_sum': sum_r(data['radiation_sum_list']),
        })
    return chart_data


# ==============================================================================
# VISTA AJAX: Carga de Datos para Gráficos (Evolución Histórica)
# ==============================================================================
@csrf_exempt 
def fetch_evolucion_ajax(request):
    """
    Maneja la solicitud AJAX para la página de Evolución Histórica.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        region_code = data.get('region_code')
        if not region_code:
            return JsonResponse({'error': 'Falta el código de la región'}, status=400)
        
        # LÓGICA "HARDCODEADA"
        if region_code == 'METROPOLITANA':
            print("--- DEVOLVIENDO DATOS 'HARDCODEADOS' (1951-2025) PARA METROPOLITANA ---")
            return JsonResponse({
                'success': True,
                'data': DATOS_METROPOLITANA
            })
        
        # Lógica antigua (para OTRAS regiones)
        print(f"--- USANDO API (4 MÉTRICAS) PARA REGIÓN: {region_code} ---")
        lat, lon = REGION_COORDS.get(region_code)
        
        API_URL = "https://archive-api.open-meteo.com/v1/archive" 
        start_date = "1950-01-01" 
        end_date = date.today().strftime('%Y-%m-%d')

        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date, 
            'monthly': 'temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum', 
            'timezone': 'auto'
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status() 
        api_data = response.json()
        
        if not api_data.get('monthly'):
             return JsonResponse({'success': False, 'message': 'API no devolvió datos mensuales.'}, status=404)

        chart_data = process_monthly_data_for_charts(api_data['monthly'])
        
        return JsonResponse({
            'success': True,
            'data': chart_data
        })
            
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'success': False, 'message': f'Error API: {response.status_code}'}, status=500)
    except Exception as e:
        print(f"Error inesperado en fetch_evolucion_ajax: {e}")
        return JsonResponse({'success': False, 'message': f'Error inesperado del servidor: {e}'}, status=500)