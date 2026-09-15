# Arquitectura local

## Límites

El producto vive separado de `growerlabs_sdd` (contexto y decisiones) y `growerlabs-infra` (automatización de plataforma). Compose es únicamente el entorno aislado de desarrollo; no describe producción.

`fuente STM → colector backend → normalizador → memoria del proceso → API → mapa`

No se ejecuta ni utiliza una base de datos. Una única captura en memoria abastece a todos los clientes y desaparece al reiniciar el proceso. No existe retención histórica de posiciones.

El Shape oficial `v_uptu_paradas` se procesa fuera del runtime: se reproyecta
de EPSG:32721 a EPSG:4326, se deduplica por código de ubicación y se convierte
en un JSON compacto. Al arrancar, FastAPI construye un índice por línea. El
navegador recibe únicamente las paradas asociadas a la empresa o línea elegida,
con un máximo de 600 elementos.

Los recorridos y aproximadamente 140 MiB de horarios CSV descomprimidos se
transforman en archivos gzip independientes por línea. Las geometrías se
simplifican con tolerancia de 8 metros antes de reproyectarse. El runtime
mantiene como máximo un archivo de línea descomprimido en caché; el refresco GPS
no vuelve a solicitar recorridos ni horarios al navegador.

La llegada aproximada se calcula bajo demanda al seleccionar una parada. El
servicio proyecta bus y parada sobre la geometría de la variante informada por
el GPS, descarta buses en otro sentido, ya pasados o alejados más de 250 metros
del trazado y estima el tiempo por distancia restante. Usa la velocidad actual
entre 8 y 40 km/h y 18 km/h cuando el coche está detenido o no informa una
velocidad útil. Es una aproximación visual, no una ETA oficial.

Leaflet separa recorrido, paradas y buses en tres paneles de dibujo con orden
350, 450 y 650 respectivamente. El recorrido puede retirarse del mapa sin
afectar las otras capas y los buses permanecen siempre por encima.

## Decisiones

- API y archivos estáticos en un contenedor FastAPI para reducir piezas en el MVP.
- Python 3.12 y dependencias fijadas para el contenedor local.
- Puerto publicado solo en loopback (`127.0.0.1:8080`).
- El cliente debe elegir empresa o línea antes de recibir posiciones; el servidor limita la respuesta a 300 coches y el contenedor a 256 MiB de RAM.
- Errores del colector conservan el último estado bueno. 403/429 activan backoff; los logs registran la clase de error, no el payload.
- `event_time` permanece vacío cuando la fuente no aporta un timestamp verificable; `received_at` es tiempo de ingesta.
- Las paradas se atribuyen a la Intendencia de Montevideo y a la Licencia de Datos Abiertos de Uruguay; el JSON conserva URL, fecha, CRS y checksum del ZIP.

## Fuentes técnicas consultadas

Consultadas el 2026-09-14: documentación oficial de FastAPI sobre imágenes propias y forma exec del comando, y contrato público observado del mapa STM. Las URLs están registradas en la evidencia de SDD-0003.
