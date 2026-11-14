# CP-2026-11-14-server-sync

Solicitud: publicar las fuentes actuales del servidor en una rama nueva, sin secretos. Cambio SDD-0008.

Repositorio: growerlabs_buses. Base: origin/checkpoint/2026-09-15-lan-quick-navigation (53ad069). Rama: checkpoint/2026-11-14-server-sync.

Se revisaron archivos, diferencias, ramas remotas y PRs relacionados; no se encontraron PRs y la base no había avanzado. Se preservó el clon previo con cambios del usuario mediante un clon independiente. Fuentes contrastadas por SHA256 con el contenedor activo durante la captura del 13 de noviembre.

Validación: 24 pruebas aprobadas; Gitleaks 8.30.1, comprobado con checksum oficial, sin hallazgos en directorio ni historial; sin direcciones privadas detectadas en fuentes. El certificado PEM existente es público, no una clave privada. Datos públicos de rutas preexistentes permanecen en el repositorio; no se incluyen bases de datos, archivos .env ni capturas privadas.

Compose requiere BUSES_DOMAIN y la red y middlewares del despliegue. Dockerfile.production reutiliza una imagen local anterior; para reconstrucción desde cero usar Dockerfile. No se ejecutó construcción ni despliegue en este checkpoint.

No hay workflow CI en este repositorio; se ejecutaron pruebas locales. El SHA final se registra en la ficha local posterior. No se modifica la rama predeterminada ni se crea PR. Reversión de código: usar la base indicada; los servicios no se modifican con esta publicación.
