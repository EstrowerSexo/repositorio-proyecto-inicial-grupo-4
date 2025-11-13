# ==============================================================================
# IMPORTACIONES CLAVE
# ==============================================================================
import requests                         
from django.shortcuts import render, redirect 
from datetime import date, timedelta 
import json
from calendar import monthrange 

# Nuevas importaciones para manejar la respuesta JSON en llamadas AJAX
from django.http import JsonResponse, Http404 
from django.views.decorators.csrf import csrf_exempt 

# Importamos las definiciones de nuestra aplicación (myapp)
from .forms import ClimaSearchForm      
from .models import REGIONES_CHOICES, RegistroClima 
from django.db.models import ObjectDoesNotExist 
today = date.today()
# ==============================================================================
# MAPEO DE DATOS (COORDENADAS) Y FONDOS REGIONALES
# ==============================================================================

REGION_COORDS = {
    'ARICA': (-18.47, -70.29),      
    'TARAPACA': (-20.22, -70.14),     
    'ANTOFAGASTA': (-23.65, -70.40),    
    'ATACAMA': (-27.36, -70.33),      
    'COQUIMBO': (-29.91, -71.25),     
    'VALPARAISO': (-33.04, -71.60),     
    'METROPOLITANA': (-33.44, -70.67),  
    'OHIGGINS': (-34.10, -70.74),     
    'MAULE': (-35.42, -71.67),      
    'NUBLE': (-36.60, -72.10),      
    'BIOBIO': (-36.82, -73.05),     
    'ARAUCANIA': (-38.73, -72.60),     
    'RIOS': (-39.81, -73.24),       
    'LAGOS': (-41.47, -72.94),      
    'AYSEN': (-45.57, -72.08),      
    'MAGALLANES': (-53.16, -70.91),     
}

REGION_BACKGROUNDS = {
    'ARICA': 'ARICA.jpg',
    'TARAPACA': 'TARAPACA.jpg',
    'ANTOFAGASTA': 'ANTOGASTA.jpg',
    'ATACAMA': 'ATACAMA.jpg',
    'COQUIMBO': 'COQUIMBO.jpg',
    'VALPARAISO': 'VALPARAISO.jpg',
    'METROPOLITANA': 'SANTIAGO.jpg',
    'OHIGGINS': 'OHIGGINS.jpg',
    'MAULE': 'MAULE.jpg',
    'NUBLE': 'NUBLE.jpg',
    'BIOBIO': 'BIOBIO.jpg',
    'ARAUCANIA': 'ARAUCANIA.jpg',
    'RIOS': 'RIOS.jpg',
    'LAGOS': 'LAGOS.jpg',
    'AYSEN': 'AYSEN.jpg',
    'MAGALLANES': 'MAGALLANES.jpg',
}

# ==============================================================================
# FUNCIÓN AUXILIAR: Cálculo de Métricas (Original)
# ==============================================================================
def calculate_metrics(daily_data):
    # Esta función se mantiene igual ya que la usa 'fetch_clima_data_ajax'
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
# VISTAS DE PÁGINA (clima_view, resultados_detalle_view, pronostico_detalle_view)
# ==============================================================================
def clima_view(request):
    form = ClimaSearchForm()
    mensaje_error = None
    if request.method == 'POST':
        form = ClimaSearchForm(request.POST)
        if form.is_valid():
            region_code = form.cleaned_data['region']
            año_buscado = form.cleaned_data['año']
            try:
                año_buscado = int(año_buscado)
                if año_buscado < 1950 or año_buscado > date.today().year:
                        mensaje_error = "Ingrese un año válido (entre 1950 y el actual)."
            except (ValueError, TypeError):
                mensaje_error = "Ingrese un año numérico válido."

            if not mensaje_error:
                lat, lon = REGION_COORDS.get(region_code)
                region_nombre = dict(REGIONES_CHOICES).get(region_code)
                request.session['clima_params'] = {
                    'region_nombre': region_nombre,
                    'region_code': region_code,
                    'año': año_buscado,
                    'lat': lat,
                    'lon': lon,
                    'is_historical': (año_buscado < date.today().year),
                }
                return redirect('resultados_detalle')

    context = { 'form': form, 'regiones': REGIONES_CHOICES, 'mensaje_error': mensaje_error }
    return render(request, 'myapp/consulta_clima.html', context)

def resultados_detalle_view(request):
    clima_params = request.session.get('clima_params', {}).copy()
    if not clima_params:
        return redirect('consulta_clima') 
    region_code = clima_params.get('region_code')
    if region_code:
        clima_params['imagen_fondo'] = REGION_BACKGROUNDS.get(region_code)
    today = date.today()
    n_days_ago = today - timedelta(days=1)
    limit_date_string = n_days_ago.strftime('%Y-%m-%d')
    year_from_form = clima_params.get('año')
    current_year = int(year_from_form) if year_from_form else today.year
    context = {
        'data': clima_params,
        'current_year': current_year,
        'current_month': today.month, 
        'limit_date': limit_date_string,
        'forecast_url': 'pronostico_detalle'
    }
    return render(request, 'myapp/resultados_detalle.html', context)

def pronostico_detalle_view(request):
    clima_params = request.session.get('clima_params', {}).copy()
    if not clima_params:
        return redirect('consulta_clima')
    region_code = clima_params.get('region_code')
    if region_code:
        clima_params['imagen_fondo'] = REGION_BACKGROUNDS.get(region_code)
    context = {
        'data': clima_params,
        'today_date_string': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'myapp/pronostico_detalle.html', context)


# ==============================================================================
# VISTAS AJAX (fetch_clima_data_ajax, fetch_pronostico_ajax)
# ==============================================================================
@csrf_exempt 
def fetch_clima_data_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

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
    
    API_URL = "https://archive-api.open-meteo.com/v1/archive" 

    if month == 0:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        periodo_label = f"Anual ({year})"
    else:
        last_day = monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        periodo_label = start_date.strftime('%B').capitalize()

    if period_end_limit:
        limit_obj = date.fromisoformat(period_end_limit)
        if month == 0:
            if year == today.year and end_date > limit_obj:
                end_date = limit_obj
        else:
            if year == today.year and month == today.month and end_date > limit_obj:
                end_date = limit_obj

    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date, 
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum,relative_humidity_2m_max', 
        'timezone': 'auto'
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status() 
        api_data = response.json()      
        
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
    
@csrf_exempt 
def fetch_pronostico_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

    region_code = data.get('region_code')
    days_offset = int(data.get('days_offset', 0))
    if not region_code:
        return JsonResponse({'error': 'Falta el código de la región'}, status=400)
    
    lat, lon = REGION_COORDS.get(region_code)
    today = date.today()
    target_date = today + timedelta(days=days_offset)
    target_date_string = target_date.strftime('%Y-%m-%d')
    
    if days_offset < 0:
        API_URL = "https://archive-api.open-meteo.com/v1/archive" 
        start_date = target_date_string
        end_date = target_date_string
        periodo_label = f"Histórico: {target_date_string}"
        is_forecast_result = False
    else:
        API_URL = "https://api.open-meteo.com/v1/forecast"
        start_date = target_date_string
        end_date = target_date_string 
        if days_offset == 0:
            periodo_label = f"Actualidad: {target_date_string}"
        else:
            periodo_label = f"Pronóstico: {target_date_string}"
        is_forecast_result = True
        
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date, 
        'hourly': 'temperature_2m',
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum,relative_humidity_2m_max', 
        'timezone': 'auto'
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status() 
        api_data = response.json()
        metrics = extract_hourly_temps(api_data)
        daily_metrics = calculate_metrics(api_data.get('daily', {}))
        
        if metrics and daily_metrics:
            final_metrics = {**metrics, **daily_metrics}
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
    

# ==============================================================================
# ==============================================================================
# NUEVO CÓDIGO: EVOLUCIÓN HISTÓRICA (CON DATOS HARCODEADOS)
# ==============================================================================
# ==============================================================================

# 1. DATOS "HARDCODEADOS" (Pegados) DE LA REGIÓN METROPOLITANA (1950-2025)
# ✅ ACTUALIZADO: AÑADIDOS LOS AÑOS 1950-1960
DATOS_METROPOLITANA = [
    # --- Nuevos datos (1950-1960) ---
    { 'year': 1950, 'temp_max_avg': 21.6, 'temp_min_avg': 9.1, 'precip_sum': 216.2, 'radiation_sum': 7824.0 },
    { 'year': 1951, 'temp_max_avg': 21.6, 'temp_min_avg': 9.6, 'precip_sum': 757.9, 'radiation_sum': 7511.6 },
    { 'year': 1952, 'temp_max_avg': 22.4, 'temp_min_avg': 10.3, 'precip_sum': 308.0, 'radiation_sum': 7754.8 },
    { 'year': 1953, 'temp_max_avg': 21.4, 'temp_min_avg': 9.6, 'precip_sum': 489.8, 'radiation_sum': 7661.3 },
    { 'year': 1954, 'temp_max_avg': 21.3, 'temp_min_avg': 9.2, 'precip_sum': 709.0, 'radiation_sum': 7438.2 },
    { 'year': 1955, 'temp_max_avg': 21.8, 'temp_min_avg': 8.8, 'precip_sum': 118.8, 'radiation_sum': 8084.1 },
    { 'year': 1956, 'temp_max_avg': 20.8, 'temp_min_avg': 8.5, 'precip_sum': 519.8, 'radiation_sum': 7651.4 },
    { 'year': 1957, 'temp_max_avg': 22.3, 'temp_min_avg': 10.0, 'precip_sum': 714.6, 'radiation_sum': 7483.9 },
    { 'year': 1958, 'temp_max_avg': 21.5, 'temp_min_avg': 9.3, 'precip_sum': 431.7, 'radiation_sum': 7501.4 },
    { 'year': 1959, 'temp_max_avg': 21.9, 'temp_min_avg': 9.4, 'precip_sum': 494.3, 'radiation_sum': 7566.2 },
    { 'year': 1960, 'temp_max_avg': 22.2, 'temp_min_avg': 9.6, 'precip_sum': 296.3, 'radiation_sum': 7831.9 },
    # --- Datos anteriores (1961-1970) ---
    { 'year': 1961, 'temp_max_avg': 21.9, 'temp_min_avg': 9.8, 'precip_sum': 385.9, 'radiation_sum': 7763.4 },
    { 'year': 1962, 'temp_max_avg': 22.3, 'temp_min_avg': 9.5, 'precip_sum': 303.7, 'radiation_sum': 7858.9 },
    { 'year': 1963, 'temp_max_avg': 19.9, 'temp_min_avg': 8.7, 'precip_sum': 561.9, 'radiation_sum': 7310.5 },
    { 'year': 1964, 'temp_max_avg': 21.2, 'temp_min_avg': 9.0, 'precip_sum': 275.1, 'radiation_sum': 7582.1 },
    { 'year': 1965, 'temp_max_avg': 20.5, 'temp_min_avg': 8.7, 'precip_sum': 543.3, 'radiation_sum': 7313.9 },
    { 'year': 1966, 'temp_max_avg': 20.3, 'temp_min_avg': 8.3, 'precip_sum': 384.8, 'radiation_sum': 7581.0 },
    { 'year': 1967, 'temp_max_avg': 20.2, 'temp_min_avg': 8.4, 'precip_sum': 278.7, 'radiation_sum': 7604.4 },
    { 'year': 1968, 'temp_max_avg': 21.5, 'temp_min_avg': 9.1, 'precip_sum': 61.6, 'radiation_sum': 7799.4 },
    { 'year': 1969, 'temp_max_avg': 21.0, 'temp_min_avg': 9.4, 'precip_sum': 376.9, 'radiation_sum': 7403.2 },
    { 'year': 1970, 'temp_max_avg': 21.0, 'temp_min_avg': 8.9, 'precip_sum': 282.9, 'radiation_sum': 7765.5 },
    # --- Datos anteriores (1971-1980) ---
    { 'year': 1971, 'temp_max_avg': 21.0, 'temp_min_avg': 8.6, 'precip_sum': 303.3, 'radiation_sum': 7761.7 },
    { 'year': 1972, 'temp_max_avg': 21.6, 'temp_min_avg': 9.8, 'precip_sum': 630.6, 'radiation_sum': 7318.9 },
    { 'year': 1973, 'temp_max_avg': 20.7, 'temp_min_avg': 9.0, 'precip_sum': 445.1, 'radiation_sum': 7598.8 },
    { 'year': 1974, 'temp_max_avg': 20.9, 'temp_min_avg': 9.0, 'precip_sum': 580.9, 'radiation_sum': 7704.8 },
    { 'year': 1975, 'temp_max_avg': 20.9, 'temp_min_avg': 8.7, 'precip_sum': 460.1, 'radiation_sum': 7606.7 },
    { 'year': 1976, 'temp_max_avg': 20.7, 'temp_min_avg': 8.3, 'precip_sum': 466.3, 'radiation_sum': 7546.0 },
    { 'year': 1977, 'temp_max_avg': 21.3, 'temp_min_avg': 9.8, 'precip_sum': 661.8, 'radiation_sum': 7584.6 },
    { 'year': 1978, 'temp_max_avg': 21.9, 'temp_min_avg': 10.2, 'precip_sum': 692.3, 'radiation_sum': 7531.8 },
    { 'year': 1979, 'temp_max_avg': 21.1, 'temp_min_avg': 9.2, 'precip_sum': 388.7, 'radiation_sum': 7396.2 },
    { 'year': 1980, 'temp_max_avg': 20.6, 'temp_min_avg': 9.0, 'precip_sum': 694.8, 'radiation_sum': 7311.3 },
    # --- Datos anteriores (1981-1990) ---
    { 'year': 1981, 'temp_max_avg': 20.9, 'temp_min_avg': 9.2, 'precip_sum': 474.8, 'radiation_sum': 7582.6 },
    { 'year': 1982, 'temp_max_avg': 20.4, 'temp_min_avg': 9.8, 'precip_sum': 1095.2, 'radiation_sum': 7081.9 },
    { 'year': 1983, 'temp_max_avg': 20.5, 'temp_min_avg': 8.8, 'precip_sum': 616.4, 'radiation_sum': 7336.2 },
    { 'year': 1984, 'temp_max_avg': 19.7, 'temp_min_avg': 8.8, 'precip_sum': 830.9, 'radiation_sum': 7281.7 },
    { 'year': 1985, 'temp_max_avg': 20.8, 'temp_min_avg': 9.1, 'precip_sum': 332.7, 'radiation_sum': 7500.4 },
    { 'year': 1986, 'temp_max_avg': 20.8, 'temp_min_avg': 9.7, 'precip_sum': 641.5, 'radiation_sum': 7239.9 },
    { 'year': 1987, 'temp_max_avg': 20.8, 'temp_min_avg': 9.5, 'precip_sum': 900.1, 'radiation_sum': 7287.1 },
    { 'year': 1988, 'temp_max_avg': 21.7, 'temp_min_avg': 9.4, 'precip_sum': 288.8, 'radiation_sum': 7794.6 },
    { 'year': 1989, 'temp_max_avg': 21.9, 'temp_min_avg': 10.0, 'precip_sum': 473.2, 'radiation_sum': 7728.1 },
    { 'year': 1990, 'temp_max_avg': 21.2, 'temp_min_avg': 9.1, 'precip_sum': 364.8, 'radiation_sum': 7547.6 },
    # --- Datos anteriores (1991-2000) ---
    { 'year': 1991, 'temp_max_avg': 20.2, 'temp_min_avg': 9.1, 'precip_sum': 658.9, 'radiation_sum': 7283.8 },
    { 'year': 1992, 'temp_max_avg': 20.2, 'temp_min_avg': 9.1, 'precip_sum': 658.9, 'radiation_sum': 7283.8 },
    { 'year': 1993, 'temp_max_avg': 20.9, 'temp_min_avg': 9.4, 'precip_sum': 434.2, 'radiation_sum': 7482.1 },
    { 'year': 1994, 'temp_max_avg': 21.4, 'temp_min_avg': 9.8, 'precip_sum': 374.8, 'radiation_sum': 7524.4 },
    { 'year': 1995, 'temp_max_avg': 21.3, 'temp_min_avg': 9.8, 'precip_sum': 386.1, 'radiation_sum': 7602.8 },
    { 'year': 1996, 'temp_max_avg': 21.5, 'temp_min_avg': 9.4, 'precip_sum': 382.5, 'radiation_sum': 7867.4 },
    { 'year': 1997, 'temp_max_avg': 21.1, 'temp_min_avg': 10.1, 'precip_sum': 1103.5, 'radiation_sum': 7300.9 },
    { 'year': 1998, 'temp_max_avg': 21.4, 'temp_min_avg': 9.4, 'precip_sum': 224.6, 'radiation_sum': 7645.4 },
    { 'year': 1999, 'temp_max_avg': 20.3, 'temp_min_avg': 9.5, 'precip_sum': 504.6, 'radiation_sum': 7509.0 },
    { 'year': 2000, 'temp_max_avg': 21.1, 'temp_min_avg': 9.7, 'precip_sum': 760.8, 'radiation_sum': 7592.9 },
    # --- Datos anteriores (2001-2010) ---
    { 'year': 2001, 'temp_max_avg': 21.1, 'temp_min_avg': 10.0, 'precip_sum': 636.3, 'radiation_sum': 7437.9 },
    { 'year': 2002, 'temp_max_avg': 21.1, 'temp_min_avg': 9.8, 'precip_sum': 807.0, 'radiation_sum': 7373.2 },
    { 'year': 2003, 'temp_max_avg': 22.0, 'temp_min_avg': 10.5, 'precip_sum': 324.4, 'radiation_sum': 7669.7 },
    { 'year': 2004, 'temp_max_avg': 21.1, 'temp_min_avg': 9.8, 'precip_sum': 535.8, 'radiation_sum': 7415.4 },
    { 'year': 2005, 'temp_max_avg': 20.8, 'temp_min_avg': 10.0, 'precip_sum': 711.2, 'radiation_sum': 7267.9 },
    { 'year': 2006, 'temp_max_avg': 21.8, 'temp_min_avg': 10.6, 'precip_sum': 542.1, 'radiation_sum': 7479.4 },
    { 'year': 2007, 'temp_max_avg': 20.4, 'temp_min_avg': 8.9, 'precip_sum': 385.1, 'radiation_sum': 7551.3 },
    { 'year': 2008, 'temp_max_avg': 21.7, 'temp_min_avg': 10.5, 'precip_sum': 433.5, 'radiation_sum': 7427.8 },
    { 'year': 2009, 'temp_max_avg': 21.7, 'temp_min_avg': 10.5, 'precip_sum': 433.5, 'radiation_sum': 7427.8 },
    { 'year': 2010, 'temp_max_avg': 20.8, 'temp_min_avg': 9.3, 'precip_sum': 416.7, 'radiation_sum': 7683.9 },
    # --- Datos anteriores (2011-2020) ---
    { 'year': 2011, 'temp_max_avg': 21.4, 'temp_min_avg': 9.5, 'precip_sum': 311.1, 'radiation_sum': 7651.8 },
    { 'year': 2012, 'temp_max_avg': 21.7, 'temp_min_avg': 10.1, 'precip_sum': 431.1, 'radiation_sum': 7452.2 },
    { 'year': 2013, 'temp_max_avg': 21.7, 'temp_min_avg': 9.8, 'precip_sum': 275.3, 'radiation_sum': 7561.6 },
    { 'year': 2014, 'temp_max_avg': 21.5, 'temp_min_avg': 9.9, 'precip_sum': 412.4, 'radiation_sum': 7501.8 },
    { 'year': 2015, 'temp_max_avg': 22.0, 'temp_min_avg': 10.5, 'precip_sum': 486.7, 'radiation_sum': 7356.3 },
    { 'year': 2016, 'temp_max_avg': 22.2, 'temp_min_avg': 10.7, 'precip_sum': 618.4, 'radiation_sum': 7320.9 },
    { 'year': 2017, 'temp_max_avg': 21.6, 'temp_min_avg': 11.2, 'precip_sum': 438.1, 'radiation_sum': 7029.3 },
    { 'year': 2018, 'temp_max_avg': 22.4, 'temp_min_avg': 11.2, 'precip_sum': 303.0, 'radiation_sum': 7127.2 },
    { 'year': 2019, 'temp_max_avg': 23.3, 'temp_min_avg': 11.3, 'precip_sum': 166.0, 'radiation_sum': 7269.9 },
    { 'year': 2020, 'temp_max_avg': 23.4, 'temp_min_avg': 11.5, 'precip_sum': 250.5, 'radiation_sum': 7500.2 },
    # --- Datos anteriores (2021-2025) ---
    { 'year': 2021, 'temp_max_avg': 22.6, 'temp_min_avg': 10.8, 'precip_sum': 302.2, 'radiation_sum': 7306.0 },
    { 'year': 2022, 'temp_max_avg': 23.1, 'temp_min_avg': 11.6, 'precip_sum': 505.4, 'radiation_sum': 6934.7 },
    { 'year': 2023, 'temp_max_avg': 23.1, 'temp_min_avg': 11.6, 'precip_sum': 505.4, 'radiation_sum': 6934.7 },
    { 'year': 2024, 'temp_max_avg': 22.9, 'temp_min_avg': 11.2, 'precip_sum': 446.1, 'radiation_sum': 7148.3 },
    { 'year': 2025, 'temp_max_avg': 22.3, 'temp_min_avg': 10.7, 'precip_sum': 351.3, 'radiation_sum': 5807.6 }
]


# 2. FUNCIÓN AYUDANTE (Simplificada para la API)
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
# VISTA (PÁGINA): Página de Evolución Histórica
# ==============================================================================
def evolucion_historica_view(request):
    """
    Renderiza la página que contendrá los gráficos de evolución histórica.
    """
    clima_params = request.session.get('clima_params', {}).copy()
    
    if not clima_params:
        return redirect('consulta_clima')
    
    region_code = clima_params.get('region_code')
    if region_code:
        clima_params['imagen_fondo'] = REGION_BACKGROUNDS.get(region_code)
    
    context = {
        'data': clima_params,
    }
    return render(request, 'myapp/evolucion_historica.html', context)


# ==============================================================================
# VISTA AJAX: Carga de Datos para Gráficos (La función REAL + Lógica RM)
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
        
        # ==================================================
        # ✅ LÓGICA "HARDCODEADA"
        # ==================================================
        if region_code == 'METROPOLITANA':
            print("--- DEVOLVIENDO DATOS 'HARDCODEADOS' (1951-2025) PARA METROPOLITANA ---")
            # Devolvemos la lista de datos que pegamos arriba
            return JsonResponse({
                'success': True,
                'data': DATOS_METROPOLITANA
            })
        # ==================================================
        
        # --- Lógica antigua (para OTRAS regiones) ---
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