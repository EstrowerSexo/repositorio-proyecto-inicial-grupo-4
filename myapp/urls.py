# ==========================================================
# CONFIGURACIÓN DE RUTAS (URLS) PARA LA APLICACIÓN 'MYAPP'
# ==========================================================

from django.urls import path
# Esta vez, importamos 'views' sabiendo que estará limpio
from . import views 

# La variable 'urlpatterns' es obligatoria en Django para definir las rutas.
urlpatterns = [
    
    # --- Rutas existentes ---
    path('', views.clima_view, name='consulta_clima'),
    path('resultados/', views.resultados_detalle_view, name='resultados_detalle'),
    path('pronostico/', views.pronostico_detalle_view, name='pronostico_detalle'),
    path('fetch_clima_data_ajax/', views.fetch_clima_data_ajax, name='fetch_clima_data_ajax'),
    path('fetch_pronostico_ajax/', views.fetch_pronostico_ajax, name='fetch_pronostico_ajax'),
    
    # =================================================================
    # NUEVO CÓDIGO: EVOLUCIÓN HISTÓRICA
    # =================================================================
    
    # RUTA 3: La página HTML
    path('evolucion/', views.evolucion_historica_view, name='evolucion_historica'),
    
    # RUTA AJAX 3: La ruta REAL para pedir los datos
    path('fetch_evolucion_ajax/', views.fetch_evolucion_ajax, name='fetch_evolucion_ajax'),
]