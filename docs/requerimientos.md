# Requerimientos Funcionales y No Funcionales - GeoForraje 1.0

Este documento define **qué** debe hacer el sistema. Las reglas de negocio que los precisan están en [`negocio.md`](negocio.md) y la relación de cada requerimiento con la API, el modelo de datos, los módulos y los tests está en [`trazabilidad.md`](trazabilidad.md).

## 1. Requerimientos Funcionales (FR)

| ID | Requerimiento | Módulo | Prioridad |
|----|---------------|--------|-----------|
| **FR-01** | **Registro de usuarios** | Auth | Alta |
| | Crear una cuenta con email, contraseña y nombre completo | | |
| | Validar el formato del email y que no esté registrado | | |
| | Contraseña de al menos 8 caracteres | | |
| | Devolver el usuario creado sin la contraseña (201) | | |
| **FR-02** | **Autenticación y sesión** | Auth | Alta |
| | Iniciar sesión y recibir un access token (15 min) y un refresh token (7 días) | | |
| | Renovar los tokens con rotación: el refresh token usado deja de servir | | |
| | Cerrar sesión invalidando el refresh token en el servidor y borrando los tokens en el cliente | | |
| | Bloquear temporalmente la cuenta ante intentos fallidos repetidos | | |
| **FR-03** | **Gestión de lotes** | Lots | Alta |
| | Crear un lote con nombre y geometría GeoJSON validada en el servidor | | |
| | Listar lotes con paginación, búsqueda por nombre y filtros (fecha, área, bounding box) | | |
| | Ver el detalle de un lote y su historial de versiones de geometría | | |
| | Editar nombre y/o geometría (cada cambio de geometría genera una versión) | | |
| | Eliminar un lote de forma **lógica**: se marca como eliminado y **sus análisis se conservan** | | |
| | Restaurar un lote eliminado | | |
| **FR-04** | **Mapa interactivo** | Map | Alta |
| | Mostrar capas base (OpenStreetMap y satélite) | | |
| | Dibujar el lote como polígono o rectángulo, editar vértices, moverlo y borrarlo | | |
| | Mostrar el área aproximada y los errores de validación mientras se dibuja | | |
| | Mostrar la geometría de un lote existente | | |
| **FR-05** | **Análisis forrajero** | Analyses | Alta |
| | Elegir una de 4 especies: alfalfa, festuca, raigrás o pastizal natural | | |
| | Recortar el mapa raster (GeoTIFF MODIS) de la especie al polígono del lote | | |
| | Calcular la tasa de crecimiento promedio (kg MS/ha/día), mínimo, máximo, desvío y percentiles | | |
| | Procesar el análisis en segundo plano y mostrar su estado (pendiente, procesando, completado, error) | | |
| | Consultar el historial de análisis de un lote y la serie temporal por especie | | |
| **FR-06** | **Protección de rutas y datos** | Auth | Alta |
| | Las rutas privadas exigen un access token válido | | |
| | Cada usuario solo ve y modifica sus propios lotes y análisis | | |
| | El frontend renueva el access token automáticamente al vencer | | |
| **FR-07** | **Panel de control** | Dashboard | Media |
| | Resumen de lotes activos, superficie total y cantidad de análisis | | |
| | Acceso rápido a los lotes y a los últimos análisis | | |
| **FR-08** | **Exportar / importar lotes** | Lots | Baja |
| | Exportar lotes a GeoJSON | | |
| | Importar geometrías desde un archivo GeoJSON | | |

## 2. Requerimientos No Funcionales (NFR)

Numeración única y correlativa, agrupada por categoría.

### Rendimiento
| ID | Requerimiento | Cómo se verifica |
|----|---------------|------------------|
| **NFR-01** | Respuesta de la API menor a 200 ms en operaciones simples | `curl -w "%{time_total}" http://localhost:8000/health` |
| **NFR-02** | Carga del mapa menor a 2 s | *Time to Interactive* en las DevTools del navegador |
| **NFR-03** | Consultas espaciales menores a 500 ms | Índice espacial GIST sobre `lots.geometry` |
| **NFR-04** | Un análisis de lote termina en menos de 5 s | Log del worker (medido: menos de 1 s) |

### Seguridad
| ID | Requerimiento | Implementación |
|----|---------------|----------------|
| **NFR-05** | Las contraseñas nunca se guardan en texto plano | bcrypt mediante `passlib` |
| **NFR-06** | Tokens JWT firmados con HS256 y clave fuera del código | `python-jose`; clave en la variable `JWT_SECRET` |
| **NFR-07** | Access token de 15 min y refresh token de 7 días, con rotación | `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `users.refresh_token_jti` |
| **NFR-08** | Contraseñas de al menos 8 caracteres | Esquema Pydantic `UserRegister` |
| **NFR-09** | Límite de intentos de login | 5 fallos bloquean la cuenta 15 min; más de 10 intentos por IP en 15 min → 429 |
| **NFR-10** | Validación de geometría en el servidor | Shapely (`is_valid`, orientación) en `lot_service.validate_geometry()` |
| **NFR-11** | CORS restringido a los orígenes configurados | `CORS_ORIGINS` |

### Arquitectura y escalabilidad
| ID | Requerimiento | Implementación |
|----|---------------|----------------|
| **NFR-12** | El procesamiento pesado no bloquea la API | Análisis en segundo plano con Celery + Redis |
| **NFR-13** | Entorno reproducible | Docker Compose (desarrollo) y `docker-compose.prod.yml` |
| **NFR-14** | Modelo preparado para multi-tenant (hoy cada lote pertenece a un usuario) | Claves UUID y propiedad por `user_id` |

### Disponibilidad y observabilidad
| ID | Requerimiento | Implementación |
|----|---------------|----------------|
| **NFR-15** | Health check y readiness | `GET /health` y `GET /ready` |
| **NFR-16** | Métricas de la API | Prometheus en `GET /metrics` |
| **NFR-17** | Documentación de la API siempre actualizada | Swagger en `/docs`, generado desde el código |

### Mantenibilidad
| ID | Requerimiento | Implementación |
|----|---------------|----------------|
| **NFR-18** | Esquema de base de datos versionado | Migraciones de Alembic |
| **NFR-19** | Código tipado y con linting | Type hints, `ruff`, TypeScript |
| **NFR-20** | Pruebas automatizadas con cobertura objetivo del 80% | `pytest` (backend) |
| **NFR-21** | Integración continua | GitHub Actions con lint + tests |

## 3. Estado de implementación (al 18/11/2026)

| ID | Estado | Observaciones |
|----|--------|---------------|
| FR-01 | ✅ Implementado | Además: verificación de email y recuperación de contraseña (los emails se registran en el log, no se envían) |
| FR-02 | ✅ Implementado | Rotación con `jti`; el logout invalida el refresh token en el servidor |
| FR-03 | ✅ Implementado | Eliminación lógica y restauración. Pendiente: el formulario de edición todavía no carga los datos del lote |
| FR-04 | ✅ Implementado | Leaflet + Geoman |
| FR-05 | ✅ Implementado | Mapas reales del 31/10/2026; la serie temporal tiene un punto por especie hasta que haya mapas de otras fechas |
| FR-06 | ✅ Implementado | |
| FR-07 | ✅ Implementado | |
| FR-08 | ❌ Pendiente | Prioridad baja; ver "Features a futuro" en el README |
| NFR-01 a NFR-03 | 🟡 Sin medir formalmente | |
| NFR-04 | ✅ Verificado | Análisis de alfalfa procesado en 0,45 s |
| NFR-05 a NFR-17 | ✅ Implementado | |
| NFR-18 | 🟡 Parcial | Las migraciones de Alembic están desactualizadas; hoy las tablas se crean desde los modelos al iniciar |
| NFR-19 | 🟡 Parcial | Tipado presente; falta configurar el linting automático |
| NFR-20 | 🟡 Parcial | 35 tests de backend; cobertura sin medir y sin tests de frontend |
| NFR-21 | ❌ Pendiente | No hay workflow de GitHub Actions |
