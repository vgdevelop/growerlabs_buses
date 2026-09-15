# Operación local y futura migración

## Comprobaciones locales

- `docker compose config` valida la composición.
- `docker compose up --build -d --wait` construye y espera salud.
- `docker compose run --rm api pytest` ejecuta contratos sintéticos.
- `GET /health` comprueba API y estado de la captura en memoria.
- `GET /metrics` expone contadores sin payloads de posiciones.

## Reversión local

`docker compose down` elimina el contenedor y la red. La captura en memoria desaparece con el proceso.

## Puerta de producción

Antes de migrar: autorización escrita de reutilización GPS; secretos externos; imágenes revisadas y fijadas por digest; capacidad y destino aprobados; proxy TLS; backup con restauración probada; RPO/RTO; límites de recursos; alertas; prueba de carga; política de retención y procedimiento de reversión. No reutilizar la contraseña de desarrollo.
