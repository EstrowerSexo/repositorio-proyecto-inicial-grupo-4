# ==============================================================================
# IMPORTACIONES CLAVE
# ==============================================================================
# Asegúrate de que 'requests' esté instalado y que 'redirect' esté en la importación
import requests                          
from django.shortcuts import render, redirect 
from datetime import date                
import json # Importamos para serializar los datos mensuales a JSON

# Importamos las definiciones de nuestra aplicación (myapp)
from .forms import ClimaSearchForm       
from .models import REGIONES_CHOICES, RegistroClima 
from django.db.models import ObjectDoesNotExist 


# ==============================================================================
# MAPEO DE DATOS (COORDENADAS) Y FONDOS REGIONALES
# ==============================================================================
# ... (REGION_COORDS y REGION_BACKGROUNDS permanecen iguales) ...

REGION_COORDS = {
    'ARICA': (-18.47, -70.29),          # Arica y Parinacota
    'TARAPACA': (-20.22, -70.14),       # Iquique
    'ANTOFAGASTA': (-23.65, -70.40),    # Antofagasta
    'ATACAMA': (-27.36, -70.33),        # Copiapó
    'COQUIMBO': (-29.91, -71.25),       # La Serena
    'VALPARAISO': (-33.04, -71.60),     # Valparaíso
    'METROPOLITANA': (-33.44, -70.67),  # Santiago (RM)
    'OHIGGINS': (-34.10, -70.74),       # Rancagua
    'MAULE': (-35.42, -71.67),          # Talca
    'NUBLE': (-36.60, -72.10),          # Chillán
    'BIOBIO': (-36.82, -73.05),         # Concepción
    'ARAUCANIA': (-38.73, -72.60),      # Temuco
    'RIOS': (-39.81, -73.24),           # Valdivia
    'LAGOS': (-41.47, -72.94),          # Puerto Montt
    'AYSEN': (-45.57, -72.08),          # Coyhaique
    'MAGALLANES': (-53.16, -70.91),     # Punta Arenas
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
# FUNCIÓN AUXILIAR: Cálculo de Métricas Mensuales
# ==============================================================================
def calculate_monthly_metrics(daily_data):
    """
    Calcula la temperatura máxima promedio y la precipitación total por mes 
    a partir de los datos diarios (Historical Archive API).
    """
    
    # Inicialización de la estructura de datos mensuales
    monthly_data = {
        month: {'temps': [], 'precip': 0.0} 
        for month in range(1, 13)
    }
    
    # Extraer arrays de la respuesta JSON de Open-Meteo
    times = daily_data['time']
    temps_max = daily_data['temperature_2m_max']
    precips = daily_data['precipitation_sum']
    
    for i, date_str in enumerate(times):
        # El formato es YYYY-MM-DD, el mes es el índice 1
        month = int(date_str.split('-')[1])
        
        # Almacenar la temperatura para calcular el promedio después
        monthly_data[month]['temps'].append(temps_max[i])
        
        # Acumular la precipitación
        monthly_data[month]['precip'] += precips[i]
        
    # Calcular promedios y finalizar el formato
    final_monthly_metrics = {}
    for month, data in monthly_data.items():
        
        # Evitar división por cero
        temp_avg = sum(data['temps']) / len(data['temps']) if data['temps'] else 0.0
        
        # Usamos el número del mes como clave del diccionario (ej: '1', '2', ...)
        final_monthly_metrics[str(month)] = {
            # Se redondean a un decimal
            'temp_avg': round(temp_avg, 1),
            'precip_sum': round(data['precip'], 1)
        }
        
    return final_monthly_metrics


# ==============================================================================
# VISTA PRINCIPAL (clima_view) - MODIFICADA PARA REDIRECCIÓN Y LÓGICA DE AÑO
# ==============================================================================

def clima_view(request):
    """
    Maneja el formulario de búsqueda. Si es exitoso, guarda datos en sesión
    y redirige a resultados_detalle_view.
    """
    
    try:
        current_year = date.today().year
    except NameError:
        current_year = 2024 # Fallback
        
    form = ClimaSearchForm(initial={'año': current_year}) 
    
    # Inicializa variables de estado
    resultado_clima = None
    mensaje_error = None
    
    # ----------------------------------------------------
    # Lógica POST (Cuando el usuario presiona 'BUSCAR CLIMA')
    # ----------------------------------------------------
    if request.method == 'POST':
        form = ClimaSearchForm(request.POST) 
        
        if form.is_valid():
            region_code = form.cleaned_data['region']
            año_buscado = form.cleaned_data['año']
            
            # 💡 Lógica para determinar si es búsqueda histórica 💡
            # Es histórico si el año buscado es menor al año actual
            is_historical = (año_buscado < current_year) 
            
            # Obtener Latitud y Longitud
            lat, lon = REGION_COORDS.get(region_code)

            # Definir el periodo de un año completo
            start_date = f"{año_buscado}-01-01"
            end_date = f"{año_buscado}-12-31" 
            
            # Configurar la Solicitud a la API de Open-Meteo
            API_URL = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': start_date,
                'end_date': end_date,
                'daily': 'temperature_2m_max,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum', 
                'timezone': 'auto' 
            }

            try:
                response = requests.get(API_URL, params=params)
                response.raise_for_status() 
                data = response.json()      
                
                if data.get('daily') and data['daily']['temperature_2m_max']:
                    
                    # Cálculo de métricas resumen (Se mantiene igual)
                    temp_max_anual = max(data['daily']['temperature_2m_max'])
                    precipitacion_total = sum(data['daily']['precipitation_sum'])
                    wind_speed_max = max(data['daily'].get('wind_speed_10m_max', [0]))
                    radiacion_total = sum(data['daily'].get('shortwave_radiation_sum', [0]))
                    
                    region_nombre = dict(REGIONES_CHOICES).get(region_code)
                    
                    # Guardar el resultado en la sesión
                    request.session['clima_data'] = {
                        'region_nombre': region_nombre,
                        'region_code': region_code, 
                        'año': año_buscado,
                        'lat': lat,                 
                        'lon': lon,                 
                        'imagen_fondo': REGION_BACKGROUNDS.get(region_code, 'default_background.jpg'), 
                        'temp_max_anual': round(temp_max_anual, 1), 
                        'precipitacion_total': round(precipitacion_total, 1),
                        'wind_speed_max': round(wind_speed_max, 1),
                        'radiacion_total': round(radiacion_total, 1),
                        'fuente': 'Open-Meteo',
                        # Incluimos los datos diarios completos para futuros cálculos mensuales
                        'daily_data': data['daily'], 
                        # 💡 NUEVA BANDERA: Para ocultar el pronóstico si es histórico
                        'is_historical': is_historical, 
                        # Temporalmente, el pronóstico está vacío (se llenará en el futuro)
                        'forecast': [], 
                    }
                    
                    # Redirigir al usuario
                    return redirect('resultados_detalle')
                    
                else:
                    mensaje_error = "La API no devolvió datos diarios para este período."
                    
            # Manejo de Errores
            except requests.exceptions.HTTPError:
                mensaje_error = f"Error al consultar la API: La solicitud falló. (Revise si el año tiene datos históricos disponibles)"
            except requests.exceptions.ConnectionError:
                mensaje_error = "Error de conexión a internet o el servicio no está disponible." 
            except Exception as e:
                mensaje_error = f"Ocurrió un error inesperado al procesar los datos: {e}"

    # Preparación del Contexto para la Plantilla HTML (Solo si falla el POST o es GET)
    context = {
        'form': form,                       
        'regiones': REGIONES_CHOICES,       
        'resultado_clima': resultado_clima, 
        'mensaje_error': mensaje_error,     
    }
    
    return render(request, 'myapp/consulta_clima.html', context)


# ==============================================================================
# VISTA DE DETALLE (resultados_detalle_view) - MODIFICADA PARA CÁLCULO MENSUAL
# ==============================================================================
def resultados_detalle_view(request):
    """
    Función que recupera los datos de clima guardados en la sesión, 
    calcula métricas mensuales y los muestra en la página de resultados detallados.
    """
    
    # 1. Obtener y borrar los datos climáticos de la sesión.
    clima_data = request.session.pop('clima_data', None)
    
    # 2. Manejo de error: Si no hay datos, redirige al formulario.
    if not clima_data:
        return redirect('consulta_clima') 

    # 💡 CÁLCULO DE MÉTRICAS MENSUALES 💡
    daily_data = clima_data.get('daily_data')
    monthly_metrics = {}
    
    if daily_data:
        # 3. Procesamos los datos para obtener los resúmenes mensuales
        monthly_metrics = calculate_monthly_metrics(daily_data)
        
    # 4. Almacenamos los datos mensuales precalculados como JSON string para JavaScript
    monthly_metrics_json = json.dumps(monthly_metrics)
    
    # 5. Preparamos el contexto para el nuevo template
    context = {
        'data': clima_data,
        'monthly_metrics_json': monthly_metrics_json, # NUEVO: Datos mensuales en formato JSON
    }
    
    # 6. Renderizamos la nueva plantilla 'resultados_detalle.html'
    return render(request, 'myapp/resultados_detalle.html', context)