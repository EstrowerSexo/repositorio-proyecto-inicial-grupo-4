# ==========================================================
# CONFIGURACIÓN DE RUTAS (URLS) PARA LA APLICACIÓN 'MYAPP'
# ==========================================================
# (Estos son tus comentarios originales)
# ==========================================================

from django.urls import path     # Función estándar para mapear patrones de URL a funciones de vista
from . import views              # Importa el módulo 'views.py' de la aplicación actual

# La variable 'urlpatterns' es obligatoria en Django para definir las rutas.
urlpatterns = [
    
    # RUTA PRINCIPAL DE LA APLICACIÓN
    # ----------------------------------
    # RUTA PRINCIPAL DE LA APLICACIÓN
    path('', views.clima_view, name='consulta_clima'),
    
    # RUTA 1: Resultados detallados (Histórico Anual/Mensual)
    path('resultados/', views.resultados_detalle_view, name='resultados_detalle'),
    
    # --------------------------------------------------------------------
    # NUEVA RUTA 2: Detalle Diario/Pronóstico (Actualidad)
    # Esta es la página de destino cuando el slider de histórico llega a 'Actualidad'.
    path('pronostico/', views.pronostico_detalle_view, name='pronostico_detalle'),
    # --------------------------------------------------------------------

    # RUTA AJAX 1: Endpoint para datos Históricos Anuales/Mensuales (usado en 'resultados_detalle.html')
    # (Nota: Se ha renombrado de 'api/fetch_data/' para un nombre más específico y sin el prefijo 'api/')
    path('fetch_clima_data_ajax/', views.fetch_clima_data_ajax, name='fetch_clima_data_ajax'),
    
    # --------------------------------------------------------------------
    # NUEVA RUTA AJAX 2: Endpoint para cargar datos Diarios (-14 a +14 días)
    # Usado en la nueva vista 'pronostico_detalle'.
    path('fetch_pronostico_ajax/', views.fetch_pronostico_ajax, name='fetch_pronostico_ajax'),
    # --------------------------------------------------------------------
    

    # =================================================================
    # INICIO DEL NUEVO CÓDIGO (PASO 2) 
    # =================================================================
    
    # RUTA 3: Nueva página para los gráficos de evolución histórica
    # Esta es la dirección para la *página HTML* que mostrará los 8 gráficos.
    path('evolucion/', views.evolucion_historica_view, name='evolucion_historica'),
    
    # RUTA AJAX 3: Endpoint para cargar TODOS los datos históricos (1950-Hoy)
    # Esta es la dirección que el *JavaScript* usará para pedir los datos 
    # y rellenar esos 8 gráficos.
    path('fetch_evolucion_ajax/', views.fetch_evolucion_ajax, name='fetch_evolucion_ajax'),
]