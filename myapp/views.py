from django.shortcuts import render # Create your views here.
from django.http import HttpResponse

def clima_view(request):
    """
    Renderiza la plantilla de consulta de clima.
    """
    # ⚠️ Asegúrate de que el nombre del archivo sea el correcto aquí
    return render(request, 'myapp/consulta_clima.html', {})