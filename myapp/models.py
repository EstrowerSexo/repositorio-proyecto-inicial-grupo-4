from django.db import models # Módulo base de modelos (para interactuar con la base de datos).

# ==============================================================================
# DEFINICIÓN DE CHOICES (LISTA DE REGIONES)
# ==============================================================================

# REGIONES_CHOICES es una lista de tuplas (clave, valor legible) que se utiliza 
# en el formulario (forms.py) y en la vista (views.py) para:
# 1. Llenar el menú desplegable en el HTML.
# 2. Mapear la clave interna (ej: 'METROPOLITANA') a sus coordenadas y a su nombre legible.
REGIONES_CHOICES = [
    ('ARICA', 'XV - Arica y Parinacota'),
    ('TARAPACA', 'I - Tarapacá'),
    ('ANTOFAGASTA', 'II - Antofagasta'),
    ('ATACAMA', 'III - Atacama'),
    ('COQUIMBO', 'IV - Coquimbo'),
    ('VALPARAISO', 'V - Valparaíso'),
    ('METROPOLITANA', 'RM - Metropolitana de Santiago'),
    ('OHIGGINS', 'VI - O\'Higgins'),
    ('MAULE', 'VII - Maule'),
    ('NUBLE', 'XVI - Ñuble'),
    ('BIOBIO', 'VIII - Biobío'),
    ('ARAUCANIA', 'IX - La Araucanía'),
    ('RIOS', 'XIV - Los Ríos'),
    ('LAGOS', 'X - Los Lagos'),
    ('AYSEN', 'XI - Aysén del G. Carlos Ibáñez del Campo'),
    ('MAGALLANES', 'XII - Magallanes y la Antártica Chilena'),
]


# ==============================================================================
# MODELO DE BASE DE DATOS (PARA FUTURAS EXPANSIONES)
# ==============================================================================

# Mantenemos la clase RegistroClima para evitar errores de importación y para 
# tener una estructura lista si decidimos guardar los resultados de la API en el futuro.
class RegistroClima(models.Model):
    
    # Campo para almacenar la región seleccionada (clave interna).
    region = models.CharField(
        max_length=50,
        choices=REGIONES_CHOICES, # Restringe las entradas a solo las opciones válidas.
        verbose_name="Región"
    )
    
    # Campo para almacenar el año consultado.
    año = models.IntegerField(
        verbose_name="Año del Registro"
    )
    
    # Campo para almacenar el resultado de la temperatura máxima anual.
    temp_max_anual = models.DecimalField(
        max_digits=5,           # Permite hasta 5 dígitos en total (ej: 123.45).
        decimal_places=2,       # Permite hasta 2 decimales.
        verbose_name="Temperatura Máxima Anual (°C)"
    )
    
    # Fecha y hora en que se creó este registro en la base de datos.
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Opciones y Metadatos del Modelo
    class Meta:
        # Asegura que no se puedan tener dos registros con la misma región y el mismo año.
        unique_together = ('region', 'año')
        verbose_name = "Registro de Clima"
        verbose_name_plural = "Registros de Clima"

    # Método que define cómo se representa el objeto en texto (útil en el panel de administración de Django).
    def __str__(self):
        return f"Clima: {self.region} - {self.año}"
