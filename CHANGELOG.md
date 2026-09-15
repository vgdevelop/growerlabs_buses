# Registro de cambios

## CP-2026-09-15-lan-quick-navigation

- Habilita acceso por red local mediante TCP 8080 restringido a `LocalSubnet`.
- Mantiene la verificación HTTPS del GPS oficial completando su cadena pública de certificados.
- Sustituye el encabezado descriptivo por accesos rápidos a 701, 706, T4R y T4N.
- Añade centros rápidos para Pando y Parque de las Ciencias sin alterar los filtros activos.
- Mejora el mensaje para líneas con GPS pero sin recorrido, paradas u horarios oficiales enlazados.
- Añade una prueba de regresión para garantizar que el colector conserva la validación TLS.

Validación: 23 pruebas, contenedor saludable, fuente GPS en vivo, SDD validado y revisión heurística sin secretos ni direcciones privadas.

## CP-2026-09-15-uruguay-buses

- Primera publicación local de la plataforma definida por SDD-0003.
- Mapa liviano limitado a Uruguay, con filtro obligatorio por empresa o línea.
- Posiciones de buses en tiempo real sin persistencia en base de datos.
- Rutas, paradas oficiales, horarios aproximados y próximas llegadas por parada.
- Capas de ruta y paradas con controles de visibilidad y modo de mapa ampliado.
- Marcadores de buses con nombre de línea, filtrado desde el detalle y seguimiento del coche seleccionado.
- Datos metropolitanos complementarios y herramientas reproducibles para regenerar índices.

Validación del checkpoint: suite automatizada, compilación de Python, configuración de Docker Compose y revisión de secretos antes de publicar.
