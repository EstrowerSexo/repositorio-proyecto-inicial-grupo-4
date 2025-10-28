from django.db import models

# Esta lista es la que da el error de importación si no está presente
REGIONES_CHOICES = [
    ('ARICA', 'XV - Arica y Parinacota'),
    ('TARAPACA', 'I - Tarapacá'),
    ('ANTOFAGASTA', 'II - Antofagagasta'),
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


# Mantenemos la clase RegistroClima para evitar futuros errores en las importaciones
# Aunque no la usaremos para guardar datos, la necesitamos para la vista.
class RegistroClima(models.Model):
    region = models.CharField(
        max_length=50,
        choices=REGIONES_CHOICES,
        verbose_name="Región"
    )
    año = models.IntegerField(
        verbose_name="Año del Registro"
    )
    temp_max_anual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Temperatura Máxima Anual (°C)"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('region', 'año')
        verbose_name = "Registro de Clima"
        verbose_name_plural = "Registros de Clima"

    def __str__(self):
        return f"Clima: {self.region} - {self.año}"
