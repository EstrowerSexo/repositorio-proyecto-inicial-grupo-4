from django.shortcuts import render
# Importamos la lista de regiones (para el menú desplegable)
from .models import REGIONES_CHOICES, RegistroClima
# Importamos el formulario que creamos para validar los datos
from .forms import ClimaSearchForm 
from django.db.models import ObjectDoesNotExist # Importar para manejar errores de búsqueda
from datetime import date

# ----------------------------------------------------
# 1. Mapeo de Regiones a Coordenadas (LAT/LON)
# ----------------------------------------------------

# La API necesita latitud y longitud. Mapeamos las regiones a un punto central.
REGION_COORDS = {
    'ARICA': (-18.47, -70.29), # Arica
    'TARAPACA': (-20.22, -70.14), # Iquique
    'ANTOFAGASTA': (-23.65, -70.40), # Antofagasta
    'ATACAMA': (-27.36, -70.33), # Copiapó
    'COQUIMBO': (-29.91, -71.25), # La Serena
    'VALPARAISO': (-33.04, -71.60), # Valparaíso
    'METROPOLITANA': (-33.44, -70.67), # Santiago
    'OHIGGINS': (-34.10, -70.74), # Rancagua
    'MAULE': (-35.42, -71.67), # Talca
    'NUBLE': (-36.60, -72.10), # Chillán
    'BIOBIO': (-36.82, -73.05), # Concepción
    'ARAUCANIA': (-38.73, -72.60), # Temuco
    'RIOS': (-39.81, -73.24), # Valdivia
    'LAGOS': (-41.47, -72.94), # Puerto Montt
    'AYSEN': (-45.57, -72.08), # Coyhaique
    'MAGALLANES': (-53.16, -70.91), # Punta Arenas
}

def clima_view(request):
    form = ClimaSearchForm(initial={'año': date.today().year}) 
    resultado_clima = None
    mensaje_error = None
    
    if request.method == 'POST':
        form = ClimaSearchForm(request.POST) 
        
        if form.is_valid():
            region_code = form.cleaned_data['region']
            año_buscado = form.cleaned_data['año']
            
            # 2. Obtener Coordenadas
            lat, lon = REGION_COORDS.get(region_code)

            # 3. Definir Fechas de Búsqueda para el Año
            start_date = f"{año_buscado}-01-01"
            end_date = f"{año_buscado}-12-31" 
            
            # 4. Construir la URL de la API
            API_URL = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': start_date,
                'end_date': end_date,
                # Variables para obtener el máximo del año
                'daily': 'temperature_2m_max,precipitation_sum',
                'timezone': 'auto' 
            }

            try:
                # 5. Hacer la Solicitud GET
                response = requests.get(API_URL, params=params)
                response.raise_for_status() # Lanza excepción si la respuesta es 4xx o 5xx
                data = response.json()
                
                # 6. Procesar la Respuesta (Ej: buscar la temperatura máxima en el año)
                if data.get('daily') and data['daily']['temperature_2m_max']:
                    # Encontramos la temperatura máxima de TODAS las máximas diarias del año
                    temp_max_anual = max(data['daily']['temperature_2m_max'])
                    
                    # Encontramos la precipitación total del año
                    precipitacion_total = sum(data['daily']['precipitation_sum'])
                    
                    # Buscamos el nombre legible de la región
                    region_nombre = dict(REGIONES_CHOICES).get(region_code)
                    
                    # Creamos el objeto de resultado
                    resultado_clima = {
                        'region_nombre': region_nombre,
                        'año': año_buscado,
                        'temp_max_anual': round(temp_max_anual, 1), # Redondeamos a un decimal
                        'precipitacion_total': round(precipitacion_total, 1),
                        'fuente': 'Open-Meteo',
                    }
                else:
                    mensaje_error = "La API no devolvió datos diarios para este período."
                    
            except requests.exceptions.HTTPError:
                mensaje_error = f"Error al consultar la API: La solicitud falló. (Revisa el año)"
            except requests.exceptions.ConnectionError:
                mensaje_error = "Error de conexión a internet o el servicio no está disponible."
            except Exception as e:
                mensaje_error = f"Ocurrió un error inesperado al procesar los datos: {e}"

    # 7. Preparación del Contexto
    context = {
        'form': form, 
        'regiones': REGIONES_CHOICES, 
        'resultado_clima': resultado_clima, 
        'mensaje_error': mensaje_error,
    }
    
    return render(request, 'myapp/consulta_clima.html', context)