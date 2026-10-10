# Requerimientos Funcionales y No Funcionales - GeoForraje 1.0

## 📋 Especificación de Requerimientos

### 1. Requerimientos Funcionales (FR)

| ID | Descripción | Módulo | Prioridad |
|----|-------------|--------|-----------|
| **FR-01** | **Registro de usuarios** | Auth | Alta |
| | - Permitir crear cuenta con email, password y nombre completo | | |
| | - Validar formato de email (EmailStr) | | |
| | - Password mínimo 8 caracteres | | |
| | - Retornar `UserPublic` sin contraseña hasheada (201) | | |
| **FR-02** | **Autenticación JWT** | Auth | Alta |
| | - Login con emisión de access_token (15 min) + refresh_token (7 días) | | |
| | - Refresh token rotation (invalida el viejo al emitir nuevo par) | | |
| | - Middleware de protección de rutas (`require_auth`) | | |
| **FR-03** | **CRUD de Lotes** | Lots | Alta |
| | - Crear lote con geometría GeoJSON validada (server-side) | | |
| | - Editar lote existente (PATCH nombre y/o geometría) | | |
| | - Eliminar lote (cascada elimina analyses asociados) | | |
| | - Listar lotes con paginación y búsqueda por nombre | | |
| **FR-04** | **Visualización Mapa** | Map/Leaflet | Alta |
| | - Cargar capas base (OSM, Satélite) | | |
| | - Dibujar polígonos con `leaflet.pm` | | |
| | - Editar y eliminar geometrías dibujadas | | |
| | - Mostrar lotes registrados como capas vectoriales | | |
| **FR-05** | **Análisis Forrajero** | Analyses | Media |
| | - Seleccionar uno de 4 recursos forrajeros | | |
| | - Consultar capa raster correspondiente | | |
| | - Calcular tasa promedio de crecimiento dentro del lote | | |
| | - Visualizar resultado obtenido | | |
| **FR-06** | **Protección de Rutas** | Auth | Alta |
| | - Rutas privadas requieren token Bearer válido | | |
| | - `GET /auth/me` retorna usuario actual | | |
| | - Refresh automático de access_token expiración | | |
| **FR-07** | **Export/Import** | Shared | Baja |
| | - Exportar lotes a GeoJSON | | |
| | - Importar geometrías validadas | | |

### 2. Requerimientos No Funcionales (NFR)

#### Rendimiento (Performance)
| Requerimiento | Especificación | Medición |
|---------------|----------------|----------|
| **NFR-01** | Tiempo de respuesta API < 200 ms | `curl -w "%{time_total}" http://localhost:8000/health` |
| **NFR-02** | Carga de mapa Leaflet < 2 segundos | `Time to Interactive` en Chrome DevTools |
| **NFR-03** | Consultas espaciales < 500 ms | PostGIS `ST_Index` en geometría lotes |
| **NFR-04** | Timout de access_token: 15 minutos | Configurable en `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` |
| **NFR-05** | Timout de refresh_token: 7 días | Configurable en `JWT_REFRESH_TOKEN_EXPIRE_DAYS` |

#### Seguridad (Security)
| Requerimiento | Especificación | Implementación |
|---------------|----------------|----------------|
| **NFR-06** | Passwords never plaintext en BD | `bcrypt.hash()` via `passlib` |
| **NFR-07** | JWT con firma HS256 | `python-jose` con `SECRET_KEY` |
| **NFR-08** | Validación de geometría server-side | `shapely.make_valid()` + validación PostGIS |
| **NFR-09** | CORS configurado origens permitidas | `["http://localhost:5173"]` |
| **NFR-10** | Contraseñas mínimo 8 caracteres con requisitos de complejidad | Validación en esquema Pydantic |

#### Escalabilidad (Scalability)
| Requerimiento | Especificación |
|---------------|----------------|
| **NFR-11** | Arquitectura preparada para multi-tenant (aunque fase 1-4 son single-user) |
| **NFR-12** | Migraciones de BD con Alembic (versiones controladas) |
| **NFR-13** | Orquestación con Docker Compose (desarrollo y producción) |

#### Disponibilidad (Availability)
| Requerimiento | Especificación |
|---------------|----------------|
| **NFR-14** | Health check endpoint en `/health` para monitoreo |
| **NFR-15** | Swagger Docs en `/docs` para validación automática |

#### Maintainability (Mantenibilidad)
| Requerimiento | Especificación |
|---------------|----------------|
| **NFR-13** | Código con type hints en 100% de funciones Python |
| **NFR-14** | Linting con `ruff` y `mypy` en CI/CD |
| **NFR-15** | Tests con coverage mínimo 80% (`make test`) |
| **NFR-16** | Formateo con `ruff format` y `prettier` |