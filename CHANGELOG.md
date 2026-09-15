# Registro de cambios

## CP-2026-09-15-uruguay-buses

- Primera publicación local de la plataforma definida por SDD-0003.
- Mapa liviano limitado a Uruguay, con filtro obligatorio por empresa o línea.
- Posiciones de buses en tiempo real sin persistencia en base de datos.
- Rutas, paradas oficiales, horarios aproximados y próximas llegadas por parada.
- Capas de ruta y paradas con controles de visibilidad y modo de mapa ampliado.
- Marcadores de buses con nombre de línea, filtrado desde el detalle y seguimiento del coche seleccionado.
- Datos metropolitanos complementarios y herramientas reproducibles para regenerar índices.

Validación del checkpoint: suite automatizada, compilación de Python, configuración de Docker Compose y revisión de secretos antes de publicar.
