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
# VISTA PRINCIPAL (clima_view)
# ==============================================================================
def clima_view(request):
    """
    Maneja el formulario de búsqueda.
    """
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

    context = {
        'form': form,
        'regiones': REGIONES_CHOICES,
        'mensaje_error': mensaje_error,
    }
    return render(request, 'myapp/consulta_clima.html', context)


# ==============================================================================
# VISTA DE DETALLE (resultados_detalle_view) - Histórico (Anual/Mensual)
# ==============================================================================
def resultados_detalle_view(request):
    """
    Muestra el detalle histórico (Anual/Mensual).
    """
    clima_params = request.session.get('clima_params', {}).copy()
    
    if not clima_params:
        return redirect('consulta_clima') 

    region_code = clima_params.get('region_code')
    if region_code:
        clima_params['imagen_fondo'] = REGION_BACKGROUNDS.get(region_code)

    today = date.today()
    DAYS_DIFFERENCE = 1 
    n_days_ago = today - timedelta(days=DAYS_DIFFERENCE)
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

# ==============================================================================
# VISTA DE DETALLE (pronostico_detalle_view) - Diario/Forecast
# ==============================================================================
def pronostico_detalle_view(request):
    """
    Muestra el detalle del pronóstico y datos diarios recientes.
    """
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
# VISTA AJAX: fetch_clima_data_ajax - Histórico (Anual/Mensual)
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
    
# ==============================================================================
# FUNCIÓN AUXILIAR: Extracción de Temperaturas por Hora (12 PM y 6 PM)
# ==============================================================================
def extract_hourly_temps(api_data):
    """
    Busca la temperatura a las 12:00 (mediodía) y 18:00 (tarde).
    """
    hourly_data = api_data.get('hourly', {})
    hourly_time = hourly_data.get('time', [])
    hourly_temp = hourly_data.get('temperature_2m', [])
    
    if not hourly_time or not hourly_temp:
        return None

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
    Maneja la solicitud AJAX para Pronóstico diario y datos históricos recientes.
    """
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
# NUEVO CÓDIGO: EVOLUCIÓN HISTÓRICA
# ==============================================================================
# ==============================================================================


# ==============================================================================
# VISTA (PÁGINA): Página de Evolución Histórica (Gráficos)
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
# FUNCIÓN AYUDANTE: Procesador de datos Mensuales -> Anuales (CORREGIDA)
# ==============================================================================
def process_monthly_data_for_charts(monthly_data):
    """
    Toma los datos mensuales de la API (ej: 900 meses)
    y los agrupa en datos anuales listos para los gráficos.
    """
    years_data = {}
    time_list = monthly_data.get('time', [])
    temp_max_means = monthly_data.get('temperature_2m_max', [])
    temp_min_means = monthly_data.get('temperature_2m_min', [])
    precips = monthly_data.get('precipitation_sum', [])
    wind_maxes = monthly_data.get('wind_speed_10m_max', [])
    radiation_sums = monthly_data.get('shortwave_radiation_sum', [])
    humidity_maxes = monthly_data.get('relative_humidity_2m_max', [])

    for i, time_str in enumerate(time_list):
        year = int(time_str[:4])
        if year not in years_data:
            years_data[year] = {
                'temp_max_list': [], 'temp_min_list': [], 'precip_sum_list': [],
                'wind_max_list': [], 'radiation_sum_list': [], 'humidity_max_list': [],
                'temp_max_abs_list': [], 'temp_min_abs_list': [],
            }
        
        # Añadir valores a las listas (CON VARIABLES CORRECTAS)
        if temp_max_means and i < len(temp_max_means) and temp_max_means[i] is not None:
            years_data[year]['temp_max_list'].append(temp_max_means[i])
            years_data[year]['temp_max_abs_list'].append(temp_max_means[i])

        if temp_min_means and i < len(temp_min_means) and temp_min_means[i] is not None:
            years_data[year]['temp_min_list'].append(temp_min_means[i])
            years_data[year]['temp_min_abs_list'].append(temp_min_means[i])
            
        if precips and i < len(precips) and precips[i] is not None:  # ✅ CORREGIDO
            years_data[year]['precip_sum_list'].append(precips[i])
            
        if wind_maxes and i < len(wind_maxes) and wind_maxes[i] is not None:  # ✅ CORREGIDO
            years_data[year]['wind_max_list'].append(wind_maxes[i])
            
        if radiation_sums and i < len(radiation_sums) and radiation_sums[i] is not None:  # ✅ CORREGIDO
            years_data[year]['radiation_sum_list'].append(radiation_sums[i])
            
        if humidity_maxes and i < len(humidity_maxes) and humidity_maxes[i] is not None:  # ✅ CORREGIDO
            years_data[year]['humidity_max_list'].append(humidity_maxes[i])

    chart_data = []
    sorted_years = sorted(years_data.keys())
    
    for year in sorted_years:
        data = years_data[year]
        
        def avg(l): return round(sum(l) / len(l), 1) if l and len(l) > 0 else 0.0
        def sum_r(l): return round(sum(l), 1) if l else 0.0
        def max_r(l): return round(max(l), 1) if l else 0.0
        def min_r(l): return round(min(l), 1) if l else 0.0

        chart_data.append({
            'year': year,
            'temp_max_avg': avg(data['temp_max_list']),
            'temp_min_avg': avg(data['temp_min_list']),
            'precip_sum': sum_r(data['precip_sum_list']),
            'wind_max': max_r(data['wind_max_list']),
            'radiation_sum': sum_r(data['radiation_sum_list']),
            'humidity_max_abs': max_r(data['humidity_max_list']),
            'temp_max_abs': max_r(data['temp_max_abs_list']),
            'temp_min_abs': min_r(data['temp_min_abs_list']),
        })
    return chart_data


# ==============================================================================
# VISTA AJAX: Carga de Datos para Gráficos (La función REAL)
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
        
        lat, lon = REGION_COORDS.get(region_code)
        if not lat or not lon:
            return JsonResponse({'error': 'Coordenadas no encontradas para la región'}, status=400)
        
        API_URL = "https://archive-api.open-meteo.com/v1/archive" 
        start_date = "1950-01-01" 
        end_date = date.today().strftime('%Y-%m-%d')

        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date, 
            'monthly': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum,relative_humidity_2m_max', 
            'timezone': 'auto'
        }

        print(f"🔍 Solicitando datos para {region_code} ({lat}, {lon}) desde {start_date} hasta {end_date}")
        
        response = requests.get(API_URL, params=params, timeout=30)  # Added timeout
        response.raise_for_status() 
        api_data = response.json()
        
        print(f"✅ API respondió con {len(api_data.get('monthly', {}).get('time', []))} registros mensuales")
        
        if not api_data.get('monthly'):
             return JsonResponse({
                 'success': False, 
                 'message': 'API no devolvió datos mensuales para el rango solicitado.'
             }, status=404)

        chart_data = process_monthly_data_for_charts(api_data['monthly'])
        
        return JsonResponse({
            'success': True,
            'data': chart_data,
            'total_years': len(chart_data)
        })
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout en la solicitud a la API")
        return JsonResponse({
            'success': False, 
            'message': 'Timeout: La API tardó demasiado en responder. Intenta con un rango más corto.'
        }, status=504)
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP {response.status_code}: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Error en la API externa: {response.status_code} - {str(e)}'
        }, status=500)
    except Exception as e:
        print(f"💥 Error inesperado en fetch_evolucion_ajax: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Error interno del servidor: {str(e)}'
        }, status=500)