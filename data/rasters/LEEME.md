# Rasters de recursos forrajeros

Poner acá los GeoTIFF (se montan en `/data/rasters` dentro de los contenedores):

| Archivo          | Recurso                          |
|------------------|----------------------------------|
| `resource_1.tif` | Biomasa verde (kg/ha)            |
| `resource_2.tif` | Cobertura suelo (%)              |
| `resource_3.tif` | Índice de vegetación (NDVI/EVI)  |
| `resource_4.tif` | Humedad suelo (%)                |

- Una sola banda (se lee la banda 1). NoData = -9999 (o el que tenga el archivo).
- Cualquier CRS: el lote (EPSG:4326) se reproyecta al CRS del raster.
- Los lotes tienen que caer dentro de la extensión del raster.
- Los `.tif` no se suben a git (ver `.gitignore`).
