# Especificación Funcional por Fases — GeoForraje 1.0

Este directorio contiene la especificación detallada de cada fase del plan de trabajo del MVP GeoForraje 1.0.

## Estructura

```
spec/printable/
├── fase_1_inicializacion_y_modelo.md
├── fase_2_autenticacion_y_usuarios.md
├── fase_3_crud_de_lotes.md
├── fase_4_leaflet_y_geometrias.md
└── fase_5_analisis_raster_y_despliegue.md
```

Cada archivo documenta:
- **Objetivo** específico de la fase
- **Artefactos** generados (archivos creados/modificados)
- **Detalle técnico** por capa (Backend, Frontend, Base de Datos)
- **Criterios de aceptación** verificables
- **Dependencias** con otras fases

## Orden de Ejecución

Las fases son **secuenciales y dependientes**:
1. **Fase 1** → Fundación: repo, README, modelo DB, migraciones base
2. **Fase 2** → Auth: registro/login JWT, protección de rutas
3. **Fase 3** → Lotes: CRUD completo + validación geométrica (requiere Fase 2)
4. **Fase 4** → Mapa: Leaflet + dibujo/edición polígonos (requiere Fase 3)
5. **Fase 5** → Análisis: Rasterio + GeoTIFF + despliegue (requiere Fase 4)

---

*Generado automáticamente como parte de la entrega "Arquitectura y Módulos + Spec por Fases"*