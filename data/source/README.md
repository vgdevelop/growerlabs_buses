# Fuente de paradas

`v_uptu_paradas.zip` es la descarga oficial de la Intendencia de Montevideo,
obtenida mediante el recurso enlazado por el Catálogo Nacional de Datos
Abiertos. El importador conserva su checksum y fecha en `app/data/stops.json`.

El ZIP no se usa durante la ejecución. El importador convierte EPSG:32721
(WGS84 / UTM 21S) a EPSG:4326 y deduplica las asociaciones parada-línea.

Los demás ZIP contienen recorridos principales, parciales y circulares, además
de horarios teóricos por parada. `tools/build_line_indexes.py` simplifica los
trazados a 8 metros y genera un archivo comprimido independiente por línea en
`app/data/lines/`. Los CSV originales no se cargan en memoria durante la
ejecución de la aplicación.

`recorridos_metropolitanos.kml` es la capa oficial de recorridos suburbanos del
MTOP, División Pasajeros - DNT, en EPSG:4326. `tools/import_mtop_routes.py` la
separa por código de empresa y línea en `app/data/metropolitan_routes/`. El KML
no se incluye en la imagen ni se carga durante la ejecución; la API abre como
máximo el índice comprimido de la selección activa. La capa aporta geometrías,
origen y destino, pero no paradas ni horarios por parada.
