from django import forms
from .models import REGIONES_CHOICES
from datetime import date

# Clase que define la estructura del formulario de búsqueda
class ClimaSearchForm(forms.Form):
    """
    Define los campos que el usuario enviará desde el formulario HTML:
    Región y Año.
    """
    
    # Campo para la Región (un menú desplegable)
    # Usamos las mismas opciones que definimos en models.py para asegurar consistencia
    region = forms.ChoiceField(
        choices=REGIONES_CHOICES,
        label='REGIÓN',
        required=True # Hacemos que la selección sea obligatoria
    )

    # Campo para el Año (un campo de texto para números)
    año = forms.IntegerField(
        label='AÑO',
        required=True, # Hacemos que el campo sea obligatorio
        # Usamos un widget (HTML) para que se parezca más a un campo de texto simple
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: 2023', 
            'maxlength': '4' # Limitamos la entrada a 4 dígitos
        })
    )

    # ----------------------------------------------------
    # 3. Validación Adicional (Lógica de Negocio)
    # ----------------------------------------------------
    
    # Este método se llama automáticamente para validar el campo 'año'
    def clean_año(self):
        año = self.cleaned_data.get('año')
        año_actual = date.today().year
        
        if año is None:
            # Esto ya debería ser manejado por 'required=True', pero es una buena práctica
            raise forms.ValidationError("El año es obligatorio.")
        
        if año < 1950 or año > año_actual:
            # No permitimos años absurdos o futuros
            raise forms.ValidationError(
                f"Por favor, ingrese un año válido entre 1900 y {año_actual}."
            )
            
        return año
