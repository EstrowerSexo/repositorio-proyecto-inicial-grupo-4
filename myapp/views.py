# ==============================================================================
# IMPORTACIONES CLAVE
# ==============================================================================
import requests                          # Librería para hacer solicitudes HTTP (necesaria para comunicarnos con la API externa).
from django.shortcuts import render      # Función estándar para cargar plantillas HTML (templates).
from datetime import date                # Necesario para obtener el año actual y pre-cargar el formulario.

# Importamos las definiciones de nuestra aplicación (myapp)
from .forms import ClimaSearchForm       # La clase de formulario que define las reglas de validación (región y año).
from .models import REGIONES_CHOICES, RegistroClima # REGIONES_CHOICES es la lista de regiones para el menú. RegistroClima
                                         # se importa para evitar errores, aunque no guardemos datos climáticos.
from django.db.models import ObjectDoesNotExist # Importar para manejar errores de búsqueda (mantener por si se usa DB).


# ==============================================================================
# MAPEO DE DATOS (COORDENADAS)
# ==============================================================================

# La API de Open-Meteo requiere la latitud (lat) y longitud (lon) de un punto.
# Mapeamos el código interno de cada región (ARICA, METROPOLITANA, etc.)
# a un par de coordenadas representativas para la búsqueda histórica.
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
# VISTA PRINCIPAL (clima_view)
# ==============================================================================

def clima_view(request):
    """
    Función que maneja todas las solicitudes a la URL /clima/.
    1. Si es GET, muestra el formulario.
    2. Si es POST, valida, consulta la API y muestra el resultado.
    """
    
    # Inicializa el formulario para mostrarlo en el HTML.
    # El valor inicial del campo 'año' se establece al año actual.
    form = ClimaSearchForm(initial={'año': date.today().year}) 
    
    # Variables de estado: se inicializan a None y se llenan solo si hay búsqueda exitosa o error.
    resultado_clima = None
    mensaje_error = None
    
    # ----------------------------------------------------
    # Lógica POST (Cuando el usuario presiona 'BUSCAR CLIMA')
    # ----------------------------------------------------
    if request.method == 'POST':
        # 1. Crear instancia del formulario con los datos enviados por el usuario
        form = ClimaSearchForm(request.POST) 
        
        # 2. Validar los datos (el formulario ejecuta las reglas de forms.py)
        if form.is_valid():
            
            # Si la validación es exitosa, los datos se obtienen de manera segura:
            region_code = form.cleaned_data['region']
            año_buscado = form.cleaned_data['año']
            
            # 3. Obtener Latitud y Longitud para la API
            # Usa .get() para evitar errores si el código de región no existe (aunque no debería pasar)
            lat, lon = REGION_COORDS.get(region_code)

            # 4. Definir el periodo de un año completo para la API
            start_date = f"{año_buscado}-01-01"
            end_date = f"{año_buscado}-12-31" 
            
            # 5. Configurar la Solicitud a la API de Open-Meteo
            API_URL = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': start_date,
                'end_date': end_date,
                # Solicitamos las variables diarias de T° máxima y Precipitación total
                'daily': 'temperature_2m_max,precipitation_sum',
                'timezone': 'auto' 
            }

            try:
                # 6. Ejecutar la Solicitud GET
                response = requests.get(API_URL, params=params)
                response.raise_for_status() # Verifica si hubo un error HTTP (4xx o 5xx)
                data = response.json()      # Convierte la respuesta JSON en un diccionario de Python
                
                # 7. Procesar y Calcular los Resultados
                if data.get('daily') and data['daily']['temperature_2m_max']:
                    
                    # Calcula la T° Máxima ANUAL (el valor más alto registrado en ese año)
                    temp_max_anual = max(data['daily']['temperature_2m_max'])
                    
                    # Calcula la Precipitación Total ANUAL (suma de la precipitación diaria)
                    precipitacion_total = sum(data['daily']['precipitation_sum'])
                    
                    # Convierte el código de región (ej: 'RM') a su nombre legible (ej: 'Metropolitana...')
                    region_nombre = dict(REGIONES_CHOICES).get(region_code)
                    
                    # 8. Guardar el Resultado para el HTML (como un diccionario)
                    resultado_clima = {
                        'region_nombre': region_nombre,
                        'año': año_buscado,
                        'temp_max_anual': round(temp_max_anual, 1), # Redondeado a 1 decimal
                        'precipitacion_total': round(precipitacion_total, 1),
                        'fuente': 'Open-Meteo',
                    }
                else:
                    mensaje_error = "La API no devolvió datos diarios para este período."
                    
            # 9. Manejo de Errores de Conexión/API
            except requests.exceptions.HTTPError:
                # Error cuando la API rechaza la solicitud (ej: año fuera del rango histórico de la API)
                mensaje_error = f"Error al consultar la API: La solicitud falló. (Revise si el año tiene datos históricos disponibles)"
            except requests.exceptions.ConnectionError:
                # Error si no hay conexión a internet o el servidor de la API está caído
                mensaje_error = "Error de conexión a internet o el servicio no está disponible."
            except Exception as e:
                # Cualquier otro error inesperado (ej: falla al procesar el JSON)
                mensaje_error = f"Ocurrió un error inesperado al procesar los datos: {e}"

    # ----------------------------------------------------
    # Preparación del Contexto para la Plantilla HTML
    # ----------------------------------------------------
    
    # El contexto es el diccionario que pasa datos de Python al HTML.
    context = {
        'form': form,                       # Pasa el formulario (contiene campos, valores ingresados y errores).
        'regiones': REGIONES_CHOICES,       # Pasa la lista completa de regiones (para llenar el <select> en HTML).
        'resultado_clima': resultado_clima, # Pasa los datos climáticos procesados (si hay éxito).
        'mensaje_error': mensaje_error,     # Pasa el mensaje de error (si ocurre).
    }
    
    # Renderiza la plantilla HTML con todos los datos del contexto.
    return render(request, 'myapp/consulta_clima.html', context)