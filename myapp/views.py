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

REGION_BACKGROUNDS = {  #editar nombres de imagenes y añadir las imagenes a la carpeta statics/img cn los mismos nombres y en jpg!!!
    'ARICA': 'ARICA.jpg',
    'TARAPACA': 'TARAPACA.jpg',
    'ANTOFAGASTA': 'ANTOGASTA.jpg',
    'ATACAMA': 'ATACAMA.jpg',
    'COQUIMBO': 'COQUIMBO.jpg',
    'VALPARAISO': 'VALPARAISO.jpg',
    'METROPOLITANA': 'SANTIAGO.jpg',
    'OHIGGINS': 'OHIGGINS.jpg',
    'MAULE': 'MAULE.jpg',
    'NUBLE': 'ÑUBLE.jpg',
    'BIOBIO': 'BIOBIO.jpg',
    'ARAUCANIA': 'ARAUCANIA.jpg',
    'RIOS': 'RIOS.jpg',
    'LAGOS': 'LAGOS.jpg',
    'AYSEN': 'AYSEN.jpg',
    'MAGALLANES': 'MAGALLANES.jpg',
}

# ==============================================================================
# VISTA PRINCIPAL (clima_view) - (Se mantiene igual)
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

            # Validar que sea numérico y razonable
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
                    'imagen_fondo': REGION_BACKGROUNDS.get(region_code, 'default_background.jpg'),
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
    Función que recupera los parámetros de clima de la sesión y muestra la plantilla.
    """
    
    clima_params = request.session.get('clima_params', None)
    
    if not clima_params:
        return redirect('consulta_clima') 

    # CÁLCULO DE FECHAS EN EL SERVIDOR
    today = date.today()
    DAYS_DIFFERENCE = 1 
    n_days_ago = today - timedelta(days=DAYS_DIFFERENCE)
    limit_date_string = n_days_ago.strftime('%Y-%m-%d')

    year_from_form = clima_params.get('año')
    if year_from_form:
        current_year = int(year_from_form)
    else:
        current_year = today.year 
    
    # Preparamos el contexto
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
    Vista para manejar el detalle del pronóstico y datos diarios recientes (-14 a +14 días).
    """
    
    clima_params = request.session.get('clima_params', None)
    
    if not clima_params:
        return redirect('consulta_clima')
    
    today = date.today()
    
    context = {
        'data': clima_params,
        'today_date_string': today.strftime('%Y-%m-%d'), # Fecha de hoy para centrar el slider
    }
    
    return render(request, 'myapp/pronostico_detalle.html', context)


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