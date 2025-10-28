from django.urls import path
from . import views  # asegúrate de que 'views.py' exista

urlpatterns = [
    # La URL será la raíz de la aplicación (ej: http://127.0.0.1:8000/clima/)
    path('', views.clima_view, name='consulta_clima'), 
]