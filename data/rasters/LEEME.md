# Mapas de tasa de crecimiento de pasturas

Poner acá los GeoTIFF (se montan en `/data/rasters` dentro de los contenedores).
Cada archivo es un mapa de **tasa de crecimiento en kg MS/ha/día** de una especie:

| Archivo        | Especie           | ID interno   |
|----------------|-------------------|--------------|
| `alfalfa.tif`  | Alfalfa           | `resource_1` |
| `festuca.tif`  | Festuca           | `resource_2` |
| `raigras.tif`  | Raigrás           | `resource_3` |
| `pastizal.tif` | Pastizal natural  | `resource_4` |

- Fecha de los mapas actuales: **31/10/2026** (versión `v2026.10.31`).
  Si se cargan mapas de otra fecha, actualizar `_FECHA_MAPAS` y `_VERSION_MAPAS`
  en `backend/app/core/raster_config.py`.
- Una sola banda (se lee la banda 1). Se usa el NoData definido en cada archivo.
- Cualquier CRS: el lote (EPSG:4326) se reproyecta al CRS del raster.
- Los lotes tienen que caer dentro de la extensión del raster; si el lote es más
  chico que un píxel, el análisis falla con "No hay datos válidos".
- Los `.tif` no se suben a git (ver `.gitignore`).
