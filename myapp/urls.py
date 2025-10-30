# ==============================================================================
# CONFIGURACIÓN DE RUTAS (URLS) PARA LA APLICACIÓN 'MYAPP'
# ==============================================================================

from django.urls import path      # Función estándar para mapear patrones de URL a funciones de vista.
from . import views               # Importa el módulo 'views.py' de la aplicación actual.

# La variable 'urlpatterns' es obligatoria en Django para definir las rutas.
urlpatterns = [
    # --------------------------------------------------------------------------
    # RUTA PRINCIPAL DE LA APLICACIÓN
    # --------------------------------------------------------------------------
    
    # RUTA PRINCIPAL DE la APLICACIÓN
    path('', views.clima_view, name='consulta_clima'), 
    
    # RUTA 1: Resultados detallados (Histórico Anual/Mensual)
    path('resultados/', views.resultados_detalle_view, name='resultados_detalle'), 
    
    # ✅ NUEVA RUTA 2: Detalle Diario/Pronóstico (Actualidad)
    #    Esta es la página de destino cuando el slider de histórico llega a 'Actualidad'.
    path('pronostico/', views.pronostico_detalle_view, name='pronostico_detalle'),
    
    # RUTA AJAX 1: Endpoint para cargar datos Históricos Anuales/Mensuales (usado en 'resultados_detalle')
    #    (Nota: Se ha renombrado de 'api/fetch_data/' para un nombre más específico y sin el prefijo 'api/')
    path('fetch_clima_data_ajax/', views.fetch_clima_data_ajax, name='fetch_clima_data_ajax'),  
    
    # ✅ NUEVA RUTA AJAX 2: Endpoint para cargar datos Diarios (-14 a +14 días)
    #    Usado en la nueva vista 'pronostico_detalle'.
    path('fetch_pronostico_ajax/', views.fetch_pronostico_ajax, name='fetch_pronostico_ajax'),
]