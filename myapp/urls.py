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
    
    # path('', views.clima_view, name='consulta_clima')
    # 1. El primer argumento ('') define la ruta: En este caso, la raíz de la aplicación 
    #    (ej: si el proyecto usa /clima/, esta ruta será http://.../clima/).
    # 2. El segundo argumento (views.clima_view) es la función Python que Django
    #    debe ejecutar cuando se accede a esta ruta.
    # 3. El tercer argumento (name='consulta_clima') es el nombre interno de la ruta.
    #    Esto es útil para referenciar la URL desde otras partes de Django (ej: en el HTML
    #    al usar {% url 'consulta_clima' %}).
    path('', views.clima_view, name='consulta_clima'), 
]
