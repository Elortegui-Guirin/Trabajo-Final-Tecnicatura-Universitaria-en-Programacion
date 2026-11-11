# Registro de cambios - GeoForraje 1.0

Formato: fecha, qué cambió y por qué. Lo más reciente arriba.

---

## 2026-11-11 — Correcciones de arranque y mapas reales

### Mapas de tasa de crecimiento
- Los 4 recursos forrajeros pasan a ser **especies**: Alfalfa, Festuca, Raigrás y Pastizal natural. Cada uno es un GeoTIFF de **tasa de crecimiento en kg MS/ha/día**, derivado de MODIS (píxel ≈ 11 ha), con fecha 31/10/2026 y cobertura de la provincia de Buenos Aires.
- Los archivos están en `data/rasters/` y se versionan en el repo.
- Los IDs internos (`resource_1..4`) se mantienen. Los nombres visibles están en `frontend/src/types/analysis.ts` y en `backend/app/core/raster_config.py`.
- Cálculo:
  - Se ignoran NoData y valores negativos (hay ~90 píxeles con artefactos negativos).
  - Los lotes más chicos que un píxel usan los píxeles que tocan.
  - Si el .tif no tiene NoData, las esquinas del recorte ya no se cuentan como 0.

### Backend: errores que impedían arrancar
- `geometry_service.py`: error de sintaxis (f-string sin cerrar).
- `report_generator.py`: paréntesis sin cerrar.
- `LotVersion` estaba definido dos veces, y el *event listener* de `lot.py` usaba argumentos inexistentes. Se dejó un solo modelo; las versiones se crean desde `lot_service`.
- La sesión de base de datos usaba el `AsyncSession` de SQLAlchemy, que no tiene `.exec()`. Se cambió por el de SQLModel.
- Tabla de usuarios:
  - Se creaba como `user` mientras las FK apuntaban a `users`. Ahora es `users`.
  - El `id` pasa a ser UUID.
  - Las fechas pasan a tener zona horaria.
- `Lot`: columnas sin tipo (`Column(None)`).
- Los IDs UUID no tenían valor por defecto.
- `Analysis`: el enum `AnalysisStatus` estaba duplicado; los enums ahora guardan el valor (`"pending"`) y `percentiles` es una columna JSON.
- `raster_config.py`: faltaba importar `Any`. El enum de recursos estaba duplicado en dos módulos.
- `schemas/analysis.py`: `ResourceTypeEnum` no era un Enum.
- Rutas con prefijo doble (`/auth/auth/login`, `/lots/lots`). Además, `/auth/refresh` y `/auth/me` estaban definidos dos veces.
- `PATCH /lots` pasaba un objeto Pydantic donde se esperaba un dict.
- Análisis: funciones async llamadas sin `await` y viceversa.
- **El análisis creaba un registro nuevo y dejaba el original en `processing` para siempre.** Ahora se completa el mismo registro.
- Celery:
  - La app no estaba registrada en la API.
  - Las tasks compartían conexiones entre event loops; ahora cada task usa su propio engine.
  - El worker de producción no escuchaba la cola `analysis`.
- `POST /analyses/check-cache` recibe un body JSON (antes eran parámetros de query).
- `pyproject.toml`:
  - Faltaban `celery` y `redis`.
  - `bcrypt` fijado a `<4.1`, porque las versiones nuevas son incompatibles con passlib.
  - `package-mode = false`, porque Poetry fallaba al no encontrar `backend/README.md`.

### Seguridad
- Rotación real del refresh token (FR-02): se guarda el `jti` vigente y el anterior queda inválido.
- La clave JWT se lee de la configuración (`JWT_SECRET`) en vez de estar escrita en el código.
- Se dejó de contar dos veces cada intento de login en el rate limit.

### Reglas de negocio
- Nombre de lote único por usuario (BR-03), sin distinguir mayúsculas. Estaba documentado pero no implementado.

### Tests
- El cliente HTTP no estaba conectado a la app; ahora usa `ASGITransport`.
- Base de prueba `geoforraje_test`, creada automáticamente y vaciada antes de cada test.
- Celery simulado en tests.
- Polígonos de prueba corregidos: el de "~100 ha" medía ~10.200 ha (más que el máximo) y el "chico" llegaba al mínimo.
- Nuevo test: nombre de lote repetido.

### Frontend
- Faltaba `index.html`, sin el cual Vite no sirve nada. También faltaba `postcss.config.js` para Tailwind.
- `App.tsx` no importaba React y no tenía el export default que usa `main.tsx`.
- La ruta de análisis por lote apuntaba a un endpoint inexistente.
- El polling de análisis usaba la firma de TanStack Query v4.
- Dockerfile: `npm ci` sin `package-lock.json`; se cambió a `npm install`.

### Frontend: mapa (reescrito)
- `leaflet.pm@^1.10.0` no existe en npm, así que `npm install` fallaba y el frontend no se construía. Se reemplazó por su sucesor, `@geoman-io/leaflet-geoman-free`.
- El módulo de mapas no podía funcionar:
  - `MapEditor` devolvía `null` hasta que existiera el mapa, y el mapa nunca se creaba.
  - La misma `ref` se usaba como `<div>` y como `L.Map`.
  - Cada capa creaba su propio mapa.
  - `DrawControl` llamaba a funciones inexistentes (`L.PM.events.draw`).
  - `MapEditor` importaba `getVertexCount` y `MAX_VERTICES`, que `useGeoJSON.ts` no exportaba, y eso hacía fallar la carga de toda la app.
- `MapEditor.tsx` se reescribió con `react-leaflet`:
  - Capas OSM y satélite.
  - Geoman para dibujar polígono o rectángulo, editar, mover y borrar.
  - Un solo polígono por lote.
  - Muestra el área aproximada y los errores de validación.
  - Mantiene la misma interfaz de props, así que `LotForm`, `LotDetail` y `AnalysisDetail` no cambian.
- `useGeoJSON.ts` reescrito: `validatePolygon`, `getVertexCount`, `calculateAreaHa` (fórmula esférica), `simplifyGeometry` y `MAX_VERTICES`.
- `LotForm` muestra los errores del servidor (área, nombre repetido) y exige dibujar el lote antes de guardar.
- `DrawControl.tsx`, `useMap.ts`, `VectorLayer.tsx` y `BaseLayers.tsx` quedaron **sin uso** y se pueden borrar.

### Frontend: errores encontrados al levantarlo
- `vite.config.ts` empezaba con un comentario `#` (sintaxis de Python), así que Vite no arrancaba.
- Errores de sintaxis por paréntesis y llaves mal cerrados en `LotList.tsx`, `LotDetail.tsx` y `LotDetailPage.tsx`.
- Los hooks de TanStack Query (`useLots`, `useLot`, `useLotVersions`, `useAnalyses`, `useAnalysis`, `useTimeSeries`) devolvían la respuesta completa de axios, pero los componentes esperan solo los datos (`data.items`, `lot.name`). Ahora devuelven `response.data`.

### Frontend: login y registro
- La página de registro **no llamaba a `/auth/register`**: solo intentaba iniciar sesión, así que las cuentas nunca se creaban.
- Después del login se pedía `/auth/me` antes de guardar el token, y el pedido salía sin autorización (401). Ahora `authApi.me(token)` recibe el token recién obtenido.
- El interceptor de refresh fallaba si no había sesión guardada (`JSON.parse(null)`). Tampoco debe intentar refrescar en login, registro o refresh. Ahora lee los tokens de forma segura.
- Los mensajes de error de la API se muestran bien, incluidos los 422 que traen una lista de errores.

### Frontend: dashboard y actualización de análisis
- El Dashboard era una página de prueba. Ahora muestra lotes activos, superficie total, cantidad de análisis, la lista de lotes con acceso a "Analizar" y los últimos análisis con su tasa.
- Las listas y el detalle de análisis se vuelven a consultar cada 2 s mientras haya alguno `pending`/`processing`. Antes el análisis se completaba en el backend, pero la pantalla seguía mostrando "Pendiente".
- `vite.config.ts` y `docker-compose.yml` usan *polling* para detectar cambios de archivos, porque Docker sobre Windows no avisa los cambios y Vite/uvicorn seguían con el código viejo.

### Backend: dependencias
- Faltaba `greenlet`, que SQLAlchemy necesita para el modo async.
- SQLAlchemy queda fijado en `>=2.0.30,<2.1`, porque `geoalchemy2` 0.14 no es compatible con SQLAlchemy 2.1 y fallaba al crear las tablas.

### Infraestructura y documentación
- Nuevo `docker-compose.yml` de desarrollo: postgres/postgis, redis, backend, worker de Celery, frontend y pgadmin.
- Documentación actualizada: README, API_SPECS, diagrama ER, reglas de negocio y estado de requerimientos.

### Pendiente
- Regenerar migraciones de Alembic.
- CI con GitHub Actions.
- Tests de frontend y typecheck.
- Export/Import GeoJSON (FR-07).
- Serie temporal con mapas de varias fechas.
- Aclarar con la fuente de los mapas:
  - Por qué alfalfa y festuca coinciden en ~17% de los píxeles.
  - Si los píxeles en 0 (≈6%, iguales en las 4 especies) son "sin crecimiento" o una máscara.
- Borrar los componentes de mapa viejos sin uso (`DrawControl`, `useMap`, `VectorLayer`, `BaseLayers`).
- Editar un lote existente: el formulario de edición todavía no carga los datos del lote.
- El `Makefile` no se pudo editar con las herramientas usadas. Agregar a mano un target `health` si se quiere.
