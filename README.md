# Grower Labs Transit

Visualizador local de SDD-0003 para las posiciones públicas actuales del STM, con fuente y cobertura explícitas. Se ejecuta en un contenedor, consulta desde backend y no persiste respuestas.

## Arranque local

1. Copiar `.env.example` como `.env` si se quieren cambiar los valores locales.
2. Ejecutar `docker compose up --build -d`.
3. Abrir `http://localhost:8080` para el mapa y `http://localhost:8080/docs` para la API.
4. Verificar con `docker compose run --rm api pytest`.
5. Detener con `docker compose down`. Agregar `-v` únicamente si se desea borrar los datos locales.

La API expone `/api/v1/sources`, `/api/v1/coverage`, `/api/v1/filters`, `/api/v1/vehicles/live`, `/api/v1/stops`, `/api/v1/lines/{line}`, `/api/v1/stops/{stop_id}/arrivals`, `/health` y `/metrics`. El colector consulta como máximo una vez cada 10 segundos para todos los clientes. La última respuesta solo existe en memoria y desaparece al detener el contenedor. `/vehicles/live` exige `company` o `line` y devuelve como máximo 300 coches. `/stops` aplica la misma selección, devuelve como máximo 600 paradas oficiales y, al elegir una línea, incorpora próximas pasadas teóricas. `/lines/{line}` devuelve únicamente los recorridos de la línea seleccionada. `/stops/{stop_id}/arrivals?line=` calcula, sin persistir, buses que todavía no pasaron por la parada y los ordena por llegada estimada. Para desactivar el colector, configurar `GPS_COLLECTION_ENABLED=false`.

## Organización

- `app/api`: rutas HTTP versionadas.
- `app/domain`: modelos canónicos y validación.
- `app/services`: caché, normalización, catálogo y colector.
- `app/static`: mapa web sin dependencias de compilación.
- `app/data`: paradas e índices comprimidos por línea y empresa; solo se abre la selección activa.
- `data/source`: snapshot de la descarga oficial y su procedencia.
- `tools`: importadores reproducibles Shape/KML → JSON compacto.
- `tools/import_mtop_routes.py`: separa los recorridos MTOP por empresa y línea.
- `tests/fixtures`: contratos sintéticos sin datos reales.
- `docs`: arquitectura, operación local y decisiones.

No hay base de datos ni configuración de producción en este incremento. La migración posterior debe definir proxy TLS, observabilidad y autorización de la fuente GPS.
