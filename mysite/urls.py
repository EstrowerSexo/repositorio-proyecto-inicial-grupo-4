# ==============================================================================
# CONFIGURACIÓN DE RUTAS (URLS) A NIVEL DE PROYECTO (MYSITE)
# ==============================================================================
"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include # 'include' es esencial para enlazar las rutas de las apps.

# La lista 'urlpatterns' mapea patrones de URL a acciones.
urlpatterns = [
    # --------------------------------------------------------------------------
    # RUTA DEL ADMINISTRADOR DE DJANGO
    # --------------------------------------------------------------------------
    # Mapea la URL '/admin/' al panel de administración de Django.
    path('admin/', admin.site.urls),
    
    # --------------------------------------------------------------------------
    # INCLUSIÓN DE LA APLICACIÓN 'CLIMA'
    # --------------------------------------------------------------------------
    # Esta es la línea clave que conecta todo:
    
    # path('clima/', include('myapp.urls'))
    # 1. El primer argumento ('clima/') define el prefijo de la URL. Todo lo que 
    #    venga después de este prefijo será manejado por 'myapp'.
    #    Ejemplo: La URL final es http://127.0.0.1:8000/clima/
    # 2. El segundo argumento (include('myapp.urls')) le dice a Django que, si 
    #    la URL comienza con 'clima/', debe buscar las rutas restantes en el 
    #    archivo 'myapp/urls.py'.
    #    Dado que 'myapp/urls.py' tiene un path('', ...), la ruta completa es '/clima/' + '' = '/clima/'.
    path('clima/', include('myapp.urls')), 
]
