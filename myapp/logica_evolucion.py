# logica_evolucion.py

import requests
import json
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict 

# La única dependencia es el mapeo de coordenadas, que está en views.py
# (Si tu proyecto usa REGION_COORDS de views.py, DEBES asegurarte de que views.py no importe nada de este archivo,
# o usa esta definición local para evitar el error de importación circular que mencionamos antes.)

REGION_NAME_MAP = {
    'METROPOLITANA': 'STGO',
    'METROPOLITANA DE SANTIAGO': 'STGO',
    'ARICA Y PARINACOTA': 'XV',
    'TARAPACÁ': 'I',
    'ANTOFAGASTA': 'II',
    'ATACAMA': 'III',
    'COQUIMBO': 'IV',
    'VALPARAÍSO': 'V',
    "O'HIGGINS": 'VI',
    'MAULE': 'VII',
    'ÑUBLE': 'XVI',
    'BIOBÍO': 'VIII',
    'LA ARAUCANÍA': 'IX',
    'LOS RÍOS': 'XIV',
    'LOS LAGOS': 'X',
    'AYSÉN': 'XI',
    'MAGALLANES': 'XII',
}
# --- 1. DEFINICIÓN LOCAL DE COORDENADAS (Incluye códigos y nombres como claves) ---
REGION_COORDS = {
    # Regiones
    'XV':   (-18.47, -70.31),  # Arica y Parinacota
    'I':    (-20.21, -70.14),  # Tarapacá
    'II':   (-23.65, -70.40),  # Antofagasta
    'III':  (-27.37, -70.33),  # Atacama
    'IV':   (-29.90, -71.25),  # Coquimbo
    'V':    (-33.04, -71.61),  # Valparaíso
    'STGO': (-33.45, -70.66),  # Metropolitana de Santiago (RM)
    'VI':   (-34.17, -70.74),  # O'Higgins
    'VII':  (-35.43, -71.65),  # Maule
    'XVI':  (-36.61, -72.10),  # Ñuble
    'VIII': (-36.82, -73.04),  # Biobío
    'IX':   (-38.74, -72.59),  # La Araucanía
    'XIV':  (-39.81, -73.25),  # Los Ríos
    'X':    (-41.47, -72.94),  # Los Lagos
    'XI':   (-45.57, -72.07),  # Aysén
    'XII':  (-53.16, -70.91),  # Magallanes
    
    # Nombres de regiones para compatibilidad con el AJAX:
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


# ==============================================================================
# FUNCIÓN DE PROCESAMIENTO: De Diario a Anual (Nueva Lógica)
# ==============================================================================
def process_daily_to_annual(daily_data):
    """
    Recibe datos DIARIOS y los agrupa en ANUALES manualmente.
    Esto imita el éxito de logica_resultado.py pero para una serie de tiempo.
    """
    if not daily_data or 'time' not in daily_data:
        return []

    # Diccionario para acumular datos por año
    # Estructura: { '1980': {'tmax': [20, 22...], 'precip': [0, 10...] } }
    annual_groups = defaultdict(lambda: {
        'tmax_list': [], 
        'tmin_list': [], 
        'precip_list': [], 
        'rad_list': []
    })

    times = daily_data.get('time', [])
    
    # Iteramos por cada día
    for i, date_str in enumerate(times):
        if not date_str: continue
        
        # Extraemos el año (los primeros 4 caracteres: "1980-01-01" -> "1980")
        year = date_str[0:4]
        
        # Obtenemos valores (manejando posibles None)
        tmax = daily_data['temperature_2m_max'][i]
        tmin = daily_data['temperature_2m_min'][i]
        prec = daily_data['precipitation_sum'][i]
        rad  = daily_data['shortwave_radiation_sum'][i]

        # Agrupamos
        group = annual_groups[year]
        if tmax is not None: group['tmax_list'].append(tmax)
        if tmin is not None: group['tmin_list'].append(tmin)
        if prec is not None: group['precip_list'].append(prec)
        if rad is not None:  group['rad_list'].append(rad)

    # Construimos el resultado final calculando promedios y sumas
    final_data = []
    sorted_years = sorted(annual_groups.keys())

    for year in sorted_years:
        g = annual_groups[year]
        
        # Solo procesamos si tenemos datos suficientes (ej. al menos 300 días para que el año sea válido)
        # O simplemente si la lista no está vacía
        if g['tmax_list'] and g['tmin_list']:
            
            # T° Max: Promedio de las máximas diarias
            avg_tmax = sum(g['tmax_list']) / len(g['tmax_list'])
            
            # T° Min: Promedio de las mínimas diarias
            avg_tmin = sum(g['tmin_list']) / len(g['tmin_list'])
            
            # Precipitación: Suma total del año
            sum_precip = sum(g['precip_list'])
            
            # Radiación: Suma total del año
            sum_rad = sum(g['rad_list'])

            final_data.append({
                'year': year,
                'temp_max_avg': round(avg_tmax, 1),
                'temp_min_avg': round(avg_tmin, 1),
                'precip_sum': round(sum_precip, 1),
                'radiation_sum': round(sum_rad, 1)
            })

    return final_data

# ==============================================================================
# VISTA AJAX PRINCIPAL
# ==============================================================================

@csrf_exempt
def fetch_evolucion_ajax(request):
    print("--- INICIO PETICIÓN AJAX EVOLUCION (MODO DIARIO -> ANUAL) ---")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        region_code_in = data.get('region_code', '').upper()
        
        # Normalizar región
        region_code = REGION_NAME_MAP.get(region_code_in, region_code_in)
        
        if not region_code or region_code not in REGION_COORDS:
            return JsonResponse({'success': False, 'message': 'Código de región no válido.'}, status=400)

        lat, lon = REGION_COORDS.get(region_code)
        print(f"Consultando: {region_code} -> {lat}, {lon}")

        # Configuración API
        API_URL = "https://archive-api.open-meteo.com/v1/archive"
        
        # CAMBIO CLAVE: Usamos 1980 como inicio seguro
        start_date = "1980-01-01" 
        end_date = date.today().strftime('%Y-%m-%d')
        
        # CAMBIO CLAVE: Solicitamos 'daily' en vez de 'monthly' (Igual que logica_resultado.py)
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,shortwave_radiation_sum',
            'timezone': 'auto'
        }

        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        
        api_data = response.json()
        
        # Verificamos si llegó 'daily' (que es lo que pedimos ahora)
        if not api_data.get('daily'):
             print("DEBUG: API no devolvió bloque 'daily'.")
             return JsonResponse({'success': False, 'message': 'Sin datos diarios.'}, status=404)

        # Procesamos: Diario -> Anual
        chart_data = process_daily_to_annual(api_data['daily'])
        
        print(f"Datos generados: {len(chart_data)} años.")

        return JsonResponse({
            'success': True,
            'data': chart_data
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error servidor: {str(e)}'}, status=500)