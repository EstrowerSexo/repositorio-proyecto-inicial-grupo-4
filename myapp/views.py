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

# ==============================================================================
# MAPEO DE DATOS (COORDENADAS) Y FONDOS REGIONALES (SE MANTIENEN IGUALES)
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
    'ARICA': 'arica_desierto.jpg',
    'TARAPACA': 'tarapaca_costa.jpg',
    'ANTOFAGASTA': 'antofagasta_desierto.jpg',
    'ATACAMA': 'atacama_florido.jpg',
    'COQUIMBO': 'coquimbo_valle.jpg',
    'VALPARAISO': 'valparaiso_puerto.jpg',
    'METROPOLITANA': 'santiago_skyline.jpg',
    'OHIGGINS': 'ohiggins_viñedo.jpg',
    'MAULE': 'maule_campo.jpg',
    'NUBLE': 'ñuble_montaña.jpg',
    'BIOBIO': 'biobio_rio.jpg',
    'ARAUCANIA': 'araucania_volcan.jpg',
    'RIOS': 'rios_valdivia.jpg',
    'LAGOS': 'lagos_osorno.jpg',
    'AYSEN': 'aysen_glaciar.jpg',
    'MAGALLANES': 'magallanes_pinguinos.jpg',
}

# ==============================================================================
# FUNCIÓN AUXILIAR: Cálculo de Métricas (Se mantiene igual)
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
    
    num_days = len(times)
    
    if num_days == 0:
        return None 
        
    temp_max_avg = round(sum(temps_max) / num_days, 1) if temps_max else 0.0
    temp_min_avg = round(sum(temps_min) / num_days, 1) if temps_min else 0.0
    
    precip_sum = round(sum(precips), 1) if precips else 0.0
    wind_max = round(max(wind_speeds), 1) if wind_speeds else 0.0
    radiation_sum = round(sum(radiation), 1) if radiation else 0.0

    return {
        'num_dias': num_days,
        'temp_max_avg': temp_max_avg, 
        'temp_min_avg': temp_min_avg, 
        'precip_sum': precip_sum,
        'wind_max': wind_max,
        'radiation_sum': radiation_sum,
        'temp_max_abs': round(max(temps_max), 1) if temps_max else 0.0,
        'temp_min_abs': round(min(temps_min), 1) if temps_min else 0.0,
    }


# ==============================================================================
# VISTA PRINCIPAL (clima_view) - (Se mantiene igual)
# ==============================================================================
def clima_view(request):
    """
    Maneja el formulario de búsqueda. Si es exitoso, guarda datos básicos en sesión
    y redirige a resultados_detalle_view.
    """
    
    current_year = date.today().year
    form = ClimaSearchForm(initial={'año': current_year}) 
    mensaje_error = None
    
    if request.method == 'POST':
        form = ClimaSearchForm(request.POST) 
        
        if form.is_valid():
            region_code = form.cleaned_data['region']
            año_buscado = form.cleaned_data['año']
            
            lat, lon = REGION_COORDS.get(region_code)
            region_nombre = dict(REGIONES_CHOICES).get(region_code)
            
            # Guardamos los parámetros necesarios para la llamada AJAX.
            request.session['clima_params'] = {
                'region_nombre': region_nombre,
                'region_code': region_code,
                'año': año_buscado,
                'lat': lat,                 
                'lon': lon,                 
                'imagen_fondo': REGION_BACKGROUNDS.get(region_code, 'default_background.jpg'), 
                'is_historical': (año_buscado < current_year), 
            }
            
            return redirect('resultados_detalle')

    context = {
        'form': form,                       
        'regiones': REGIONES_CHOICES,       
        'mensaje_error': mensaje_error,     
    }
    
    return render(request, 'myapp/consulta_clima.html', context)


# ==============================================================================
# VISTA DE DETALLE (resultados_detalle_view) - ✅ MODIFICADA PARA TESTEO
# ==============================================================================
def resultados_detalle_view(request):
    """
    Función que recupera los parámetros de clima de la sesión y muestra la plantilla.
    Añade variables de fecha actual para el control del slider en JS.
    """
    
    clima_params = request.session.get('clima_params', None)
    
    if not clima_params:
        return redirect('consulta_clima') 

    # CÁLCULO DE FECHAS EN EL SERVIDOR
    today = date.today()
    
    # 🚨🚨🚨 PUNTO CLAVE PARA PROBAR 🚨🚨🚨
    # Hemos aumentado la diferencia a 3 días como prueba.
    DAYS_DIFFERENCE = 1 
    
    # La fecha límite para datos históricos
    n_days_ago = today - timedelta(days=DAYS_DIFFERENCE)
    
    # Formato de fecha para pasar a JavaScript (ej: "2025-10-26" si hoy es 29 y DAYS_DIFFERENCE=3)
    limit_date_string = n_days_ago.strftime('%Y-%m-%d')
    
    # Preparamos el contexto
    context = {
        'data': clima_params,
        'current_year': today.year,
        'current_month': today.month, # 1 (Enero) a 12 (Diciembre)
        'limit_date': limit_date_string, # Enviamos la fecha límite
    }
    
    return render(request, 'myapp/resultados_detalle.html', context)


# ==============================================================================
# VISTA AJAX: fetch_clima_data_ajax - (Usa la variable enviada por resultados_detalle_view)
# ==============================================================================
@csrf_exempt 
def fetch_clima_data_ajax(request):
    """
    Maneja la solicitud AJAX (POST) desde el slider, llamando a Open-Meteo
    para el periodo solicitado (histórico o forecast) y devuelve el resumen JSON.
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
    month = int(data.get('month')) # 0 = Anual, 99 = Actualidad/Forecast (Forecast ahora es month 99)
    
    # NUEVOS PARÁMETROS DE CONTROL
    is_forecast = data.get('is_forecast', False) # True si se selecciona "Actualidad"
    # period_end contendrá la fecha límite (por defecto, ayer o hace N días)
    period_end_limit = data.get('period_end')    

    if not region_code:
        return JsonResponse({'error': 'Falta el código de la región'}, status=400)
    
    lat, lon = REGION_COORDS.get(region_code)

    # 2. Definir Fechas y API URL
    
    # LÓGICA DE FORECAST (Actualidad) - Usa la API de Open-Meteo V1
    if is_forecast:
        API_URL = "https://api.open-meteo.com/v1/forecast" 
        periodo_label = f"Actualidad (Pronóstico y datos en vivo)"
        
        # Parámetros para el Forecast (7 días por defecto)
        params = {
            'latitude': lat,
            'longitude': lon,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum', 
            'current_weather': True, 
            'timezone': 'auto' 
        }
    
    # LÓGICA DE HISTÓRICO (Slider) - Usa la API de ARCHIVE
    else:
        API_URL = "https://archive-api.open-meteo.com/v1/archive" 

        # 2a. Definir Fechas de Inicio y Fin basadas en el mes para el ARCHIVE
        if month == 0: # Anual
            start_date = f"{year}-01-01"
            
            # Si tenemos un límite (viene del JS), lo usamos como fin de año. Si no, usamos el 31 de Dic.
            end_date = period_end_limit if period_end_limit else f"{year}-12-31" 
            periodo_label = f"Anual ({year})"
        
        else: # Mensual (month es 1-12)
            start_date = f"{year}-{month:02d}-01"
            
            # 1. Calcular el último día del mes por defecto
            _, last_day = monthrange(year, month) 
            end_date_default = date(year, month, last_day).strftime('%Y-%m-%d')
            
            # 2. Asumimos el fin de mes por defecto
            end_date = end_date_default
            
            # 3. COMPROBACIÓN CLAVE: Si hay un límite (`period_end_limit`) enviado desde JS, lo aplicamos.
            if period_end_limit:
                # Convertimos ambas a objetos date para la comparación
                limit_date_obj = date.fromisoformat(period_end_limit)
                end_date_obj = date.fromisoformat(end_date_default)
                start_date_obj = date.fromisoformat(start_date)

                # Si el fin de mes es posterior al límite Y el mes de inicio es anterior o igual al límite,
                # USAMOS el límite.
                if end_date_obj > limit_date_obj and start_date_obj <= limit_date_obj:
                    end_date = period_end_limit
                
                # Manejo de error si el mes completo está fuera del rango permitido (esto debería ser manejado en JS)
                elif start_date_obj > limit_date_obj:
                    return JsonResponse({'success': False, 'message': f'El mes {month} aún no tiene datos históricos disponibles (límite: {period_end_limit}).'}, status=404)


            periodo_label = date(year, month, 1).strftime('%B').capitalize() 

        # Parámetros para el Archive
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date, # Usamos la fecha ajustada
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum', 
            'timezone': 'auto' 
        }

    # 3. Solicitud a la API de Open-Meteo
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status() 
        api_data = response.json()      
        
        # 4. Procesar la respuesta
        if api_data.get('daily'):
            metrics = calculate_metrics(api_data['daily'])
            
            if metrics:
                # 5. Devolver las métricas resumidas como JSON
                return JsonResponse({
                    'success': True,
                    'periodo_label': periodo_label,
                    'metrics': metrics,
                    'is_forecast_result': is_forecast
                })
            else:
                return JsonResponse({'success': False, 'message': 'API no devolvió datos diarios para este periodo.'}, status=404)
        
        # Manejo específico para Forecast si no devuelve métricas diarias
        elif is_forecast and api_data.get('current_weather'):
             return JsonResponse({'success': False, 'message': 'API de pronóstico devolvió datos insuficientes para un resumen de periodo.'}, status=404)
        else:
            return JsonResponse({'success': False, 'message': 'API no devolvió datos diarios para este periodo.'}, status=404)
            
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'success': False, 'message': f'Error API: El servidor externo devolvió un error ({response.status_code}).'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error inesperado del servidor: {e}'}, status=500)