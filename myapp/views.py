# ==============================================================================
# IMPORTACIONES CLAVE
# ==============================================================================
import requests                          # Librería para hacer solicitudes HTTP (necesaria para comunicarnos con la API externa).
# MODIFICACIÓN CLAVE: Importamos 'redirect' para poder redirigir a la página de resultados.
from django.shortcuts import render, redirect # Función estándar para cargar plantillas HTML (templates).
from datetime import date                # Necesario para obtener el año actual y pre-cargar el formulario.

# Importamos las definiciones de nuestra aplicación (myapp)
from .forms import ClimaSearchForm       # La clase de formulario que define las reglas de validación (región y año).
from .models import REGIONES_CHOICES, RegistroClima # REGIONES_CHOICES es la lista de regiones para el menú. RegistroClima
                                         # se importa para evitar errores.
from django.db.models import ObjectDoesNotExist # Importar para manejar errores de búsqueda (mantener por si se usa DB).


# ==============================================================================
# MAPEO DE DATOS (COORDENADAS)
# ==============================================================================

# La API de Open-Meteo requiere la latitud (lat) y longitud (lon) de un punto.
# Mapeamos el código interno de cada región a coordenadas representativas.
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


# ==============================================================================
# VISTA PRINCIPAL (clima_view) - MODIFICADA PARA REDIRECCIÓN
# ==============================================================================

def clima_view(request):
    """
    Maneja el formulario de búsqueda. Si es exitoso, guarda datos en sesión
    y redirige a resultados_detalle_view.
    """
    
    # Inicializa el formulario con el año actual por defecto
    form = ClimaSearchForm(initial={'año': date.today().year}) 
    
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
                'daily': 'temperature_2m_max,precipitation_sum',
                'timezone': 'auto' 
            }

            try:
                # 6. Ejecutar la Solicitud GET
                response = requests.get(API_URL, params=params)
                response.raise_for_status() 
                data = response.json()      
                
                # 7. Procesar y Calcular los Resultados
                if data.get('daily') and data['daily']['temperature_2m_max']:
                    
                    # Cálculo de métricas resumen
                    temp_max_anual = max(data['daily']['temperature_2m_max'])
                    precipitacion_total = sum(data['daily']['precipitation_sum'])
                    region_nombre = dict(REGIONES_CHOICES).get(region_code)
                    
                    # NUEVO PASO 8: Guardar el resultado en la sesión
                    # Usamos la sesión de Django para transferir los datos a la próxima vista.
                    request.session['clima_data'] = {
                        'region_nombre': region_nombre,
                        'region_code': region_code, 
                        'año': año_buscado,
                        'temp_max_anual': round(temp_max_anual, 1), 
                        'precipitacion_total': round(precipitacion_total, 1),
                        'fuente': 'Open-Meteo',
                        # NOTA: Si necesitas los datos mensuales, incluir aquí: 'daily_data': data['daily'],
                    }
                    
                    # NUEVO PASO 9: Redirigir al usuario
                    return redirect('resultados_detalle')
                    
                else:
                    mensaje_error = "La API no devolvió datos diarios para este período."
                    
            # 10. Manejo de Errores
            except requests.exceptions.HTTPError:
                mensaje_error = f"Error al consultar la API: La solicitud falló. (Revise si el año tiene datos históricos disponibles)"
            except requests.exceptions.ConnectionError:
                # ¡IMPORTANTE! Se corrige la línea para cerrar la comilla y evitar el SyntaxError anterior.
                mensaje_error = "Error de conexión a internet o el servicio no está disponible." 
            except Exception as e:
                mensaje_error = f"Ocurrió un error inesperado al procesar los datos: {e}"

    # ----------------------------------------------------
    # Preparación del Contexto para la Plantilla HTML (Solo si falla el POST o es GET)
    # ----------------------------------------------------
    context = {
        'form': form,                       
        'regiones': REGIONES_CHOICES,       
        'resultado_clima': resultado_clima, 
        'mensaje_error': mensaje_error,     
    }
    
    return render(request, 'myapp/consulta_clima.html', context)


# ==============================================================================
# NUEVA VISTA: resultados_detalle_view (Función que estaba faltando)
# ==============================================================================
def resultados_detalle_view(request):
    """
    Función que recupera los datos de clima guardados en la sesión y los 
    muestra en la nueva página de resultados detallados.
    """
    
    # 1. Obtener y borrar los datos climáticos de la sesión.
    # .pop('clima_data', None) toma el dato y lo elimina, o devuelve None si no existe.
    clima_data = request.session.pop('clima_data', None)
    
    # 2. Manejo de error: Si no hay datos, redirige al formulario.
    if not clima_data:
        return redirect('consulta_clima') 

    # 3. Preparamos el contexto para el nuevo template
    context = {
        'data': clima_data,
        # Placeholder para datos futuros
        'data_climatologicos_mensuales': {
             'T. Máx': ['...', '...'], 
             'Precipitación': ['...', '...'],
        }
    }
    
    # 4. Renderizamos la nueva plantilla 'resultados_detalle.html'
    return render(request, 'myapp/resultados_detalle.html', context)