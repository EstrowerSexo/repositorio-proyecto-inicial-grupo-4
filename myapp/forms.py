from django import forms                 # Módulo base de formularios de Django.
from .models import REGIONES_CHOICES     # Importamos la lista de tuplas de regiones desde models.py.
from datetime import date                # Necesario para obtener el año actual en la validación.

# ==============================================================================
# CLASE DEL FORMULARIO DE BÚSQUEDA
# ==============================================================================

class ClimaSearchForm(forms.Form):
    """
    Define los campos que el usuario enviará desde el formulario HTML: Región y Año.
    Esta clase se encarga de:
    1. Generar el HTML de los campos.
    2. Recibir y limpiar los datos.
    3. Aplicar las validaciones básicas y personalizadas.
    """
    
    # ----------------------------------------------------
    # 1. Definición del Campo 'Región' (Select/Desplegable)
    # ----------------------------------------------------
    region = forms.ChoiceField(
        choices=REGIONES_CHOICES,        # Opciones para el menú desplegable, tomadas de models.py.
        label='REGIÓN',                  # Etiqueta que se mostrará en el HTML.
        required=True                    # Hace que la selección sea obligatoria (validación básica).
    )

    # ----------------------------------------------------
    # 2. Definición del Campo 'Año' (Entrada de Texto Numérica)
    # ----------------------------------------------------
    año = forms.IntegerField(
        label='AÑO',                     # Etiqueta que se mostrará en el HTML.
        required=True,                   # El campo es obligatorio.
        # Definimos el Widget: Es la representación HTML del campo.
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: 2023',   # Texto de ejemplo dentro del campo.
            'maxlength': '4',            # Limita la entrada a 4 dígitos en el navegador.
            'type': 'number'             # (Aunque usamos TextInput, forzamos type='number' si el framework lo permite).
        })
    )

    # ----------------------------------------------------
    # 3. Validación Personalizada del Campo 'Año'
    # ----------------------------------------------------
    
    # El método 'clean_<nombre_del_campo>' es una validación específica de Django.
    # Se llama automáticamente después de las validaciones básicas (como 'required=True').
    def clean_año(self):
        # Obtiene el valor del año ya limpiado y convertido a Integer.
        año = self.cleaned_data.get('año')
        año_actual = date.today().year
        
        if año is None:
            # Aunque 'required=True' debe manejar esto, se incluye como doble seguridad.
            raise forms.ValidationError("El año es obligatorio.")
        
        # Lógica de Negocio: Restricción del rango de años
        # Se asume que la API (Open-Meteo) tiene datos históricos desde 1950.
        # Se restringe hasta el año actual para evitar búsquedas en el futuro.
        if año < 1950 or año > año_actual:
            raise forms.ValidationError(
                f"Por favor, ingrese un año válido entre 1950 y {año_actual}."
            )
            
        return año # El dato debe retornarse limpio para que el proceso continúe.
