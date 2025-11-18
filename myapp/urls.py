# ==========================================================
# CONFIGURACIÓN DE RUTAS (URLS) PARA LA APLICACIÓN 'MYAPP'
# ==========================================================

from django.urls import path
from . import views 

# 🆕 Importar las funciones de lógica desde los nuevos módulos
from .logica_resultado import fetch_clima_data_ajax
from .logica_pronostico import fetch_pronostico_ajax 
from .logica_evolucion import fetch_evolucion_ajax

# La variable 'urlpatterns' es obligatoria en Django para definir las rutas.
urlpatterns = [
    
    # --- Rutas de Vistas (siguen en views.py) ---
    path('', views.clima_view, name='consulta_clima'),
    path('resultados/', views.resultados_detalle_view, name='resultados_detalle'),
    path('pronostico/', views.pronostico_detalle_view, name='pronostico_detalle'),
    path('evolucion/', views.evolucion_historica_view, name='evolucion_historica'),
    
    # --- Rutas AJAX (ahora apuntan a las funciones importadas) ---
    # La lógica de resultados_detalle_view (Anual/Mensual)
    path('fetch_clima_data_ajax/', fetch_clima_data_ajax, name='fetch_clima_data_ajax'),
    
    # La lógica de pronostico_detalle_view (Diario/Forecast)
    path('fetch_pronostico_ajax/', fetch_pronostico_ajax, name='fetch_pronostico_ajax'),
    
    # La lógica de Evolución Histórica (Gráficos)
    path('fetch_evolucion_ajax/', fetch_evolucion_ajax, name='fetch_evolucion_ajax'),
]