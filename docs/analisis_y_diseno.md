# Análisis y Diseño - GeoForraje 1.0

Artefactos de análisis y diseño del sistema: casos de uso, diagramas de actividades, diagrama de estados del análisis y diagrama de clases. Los diagramas están en Mermaid y GitHub los muestra dibujados. Complementa [`requerimientos.md`](requerimientos.md), [`negocio.md`](negocio.md), [`arquitectura.md`](arquitectura.md) y [`diagrama_er.md`](diagrama_er.md).

## 1. Actores

| Actor | Descripción |
|-------|-------------|
| **Visitante** | Persona sin sesión iniciada: puede registrarse o iniciar sesión |
| **Productor / asesor** (usuario registrado) | Gestiona sus lotes y pide análisis de crecimiento de pasturas |
| **Worker de análisis** (actor de sistema) | Proceso Celery que calcula los análisis en segundo plano |

## 2. Diagrama de casos de uso

```mermaid
flowchart LR
    V(["👤 Visitante"])
    P(["👤 Productor / asesor"])
    W(["⚙️ Worker de análisis"])

    subgraph SIS["GeoForraje"]
        CU01(["CU-01 Registrarse"])
        CU02(["CU-02 Iniciar sesión"])
        CU03(["CU-03 Cerrar sesión"])
        CU04(["CU-04 Crear lote dibujándolo"])
        CU05(["CU-05 Consultar lotes"])
        CU06(["CU-06 Editar lote"])
        CU07(["CU-07 Eliminar / restaurar lote"])
        CU08(["CU-08 Analizar lote por especie"])
        CU09(["CU-09 Consultar resultados"])
        CU10(["CU-10 Ver panel de control"])
        CU11(["CU-11 Procesar análisis"])
        CU12(["CU-12 Validar geometría"])
    end

    V --- CU01
    V --- CU02
    P --- CU03
    P --- CU04
    P --- CU05
    P --- CU06
    P --- CU07
    P --- CU08
    P --- CU09
    P --- CU10
    CU11 --- W

    CU04 -. include .-> CU12
    CU06 -. include .-> CU12
    CU08 -. include .-> CU11
```

## 3. Especificación de casos de uso

| ID | Caso de uso | Actor | Flujo principal | Flujos alternativos | Reglas |
|----|-------------|-------|-----------------|---------------------|--------|
| **CU-01** | Registrarse | Visitante | 1. Completa nombre, email y contraseña. 2. El sistema crea la cuenta. 3. Inicia sesión automáticamente | Email ya registrado → 400. Contraseña de menos de 8 caracteres → error de validación | RN-AUTH-01 |
| **CU-02** | Iniciar sesión | Visitante | 1. Ingresa email y contraseña. 2. Recibe access y refresh token. 3. Entra al panel de control | Credenciales inválidas → 401. 5 fallos → cuenta bloqueada 15 min (423). Muchos intentos por IP → 429 | RN-AUTH-02, RN-AUTH-05, RN-AUTH-07 |
| **CU-03** | Cerrar sesión | Productor | 1. Toca "Cerrar sesión". 2. El servidor invalida el refresh token. 3. El cliente borra los tokens y va a `/login` | Sin conexión: igual se cierra la sesión local | RN-AUTH-06 |
| **CU-04** | Crear lote | Productor | 1. Abre "Nuevo lote". 2. Dibuja el polígono o rectángulo en el mapa. 3. Ve el área aproximada. 4. Pone un nombre y guarda. 5. El sistema valida, calcula el área oficial y crea la versión 1 | Polígono inválido o área fuera de rango → 422. Nombre repetido → 422 | RN-GEO-01 a 07, RN-LOT-02, RN-LOT-03 |
| **CU-05** | Consultar lotes | Productor | 1. Abre "Mis lotes". 2. Filtra por nombre, fecha, área o zona. 3. Abre el detalle con el mapa y el historial de versiones | Sin lotes → invitación a crear uno | RN-LOT-01 |
| **CU-06** | Editar lote | Productor | 1. Cambia el nombre y/o redibuja el polígono. 2. Indica un motivo. 3. El sistema guarda y, si cambió la geometría, agrega una versión | Mismas validaciones que CU-04 | RN-LOT-03 |
| **CU-07** | Eliminar / restaurar lote | Productor | 1. Elimina el lote (se marca como eliminado). 2. Lo ve tildando "Mostrar lotes eliminados" en el listado y puede restaurarlo | — | RN-LOT-04, RN-LOT-05 |
| **CU-08** | Analizar lote por especie | Productor | 1. En el lote elige una especie (alfalfa, festuca, raigrás o pastizal). 2. El sistema crea el análisis en estado pendiente y lo encola. 3. La pantalla se actualiza sola hasta que termina | Ya existe el mismo análisis → se devuelve el guardado. Hay uno en curso → 409 | RN-ANA-01, RN-ANA-07, RN-ANA-08 |
| **CU-09** | Consultar resultados | Productor | 1. Ve el historial de análisis del lote. 2. Abre uno: tasa promedio, mínimo, máximo, desvío y percentiles | Análisis fallido → se muestra el motivo | RN-ANA-02, RN-ANA-06 |
| **CU-10** | Ver panel de control | Productor | Ve lotes activos, superficie total, cantidad de análisis y los últimos resultados | — | — |
| **CU-11** | Procesar análisis | Worker | 1. Toma la tarea. 2. Pasa el análisis a `processing`. 3. Recorta el mapa de la especie al lote. 4. Calcula las estadísticas. 5. Guarda `completed` | Lote fuera del mapa o sin datos → `failed` con mensaje | RN-ANA-02 a 06 |
| **CU-12** | Validar geometría | Sistema | Verifica tipo, validez, orientación, área y nombre | Cualquier falla → 422 con el motivo | RN-GEO-01 a 06 |

## 4. Diagrama de actividades: crear un lote (CU-04)

```mermaid
flowchart TD
    A([Inicio]) --> B[Abrir 'Nuevo lote']
    B --> C[Dibujar polígono en el mapa]
    C --> D{¿Polígono válido y área<br/>entre 0,01 y 10.000 ha?<br/>validación en el navegador}
    D -- No --> E[Mostrar errores en el mapa] --> C
    D -- Sí --> F[Ingresar nombre y guardar]
    F --> G[API: validar polígono con Shapely<br/>y calcular área en UTM]
    G --> H{¿Válido, área en rango<br/>y nombre único?}
    H -- No --> I[Responder 422 con el motivo] --> J[Mostrar error en el formulario] --> F
    H -- Sí --> K[Guardar lote en PostGIS]
    K --> L[Crear versión 1 en lot_versions]
    L --> M[Responder 201 con el área oficial]
    M --> N([Lote visible en 'Mis lotes'])
```

## 5. Diagrama de actividades: analizar un lote (CU-08 + CU-11)

```mermaid
flowchart TD
    A([Productor elige especie]) --> B[POST /analyses]
    B --> C{¿Lote propio?}
    C -- No --> C1[404] --> Z([Fin])
    C -- Sí --> D{¿Existe un análisis completado<br/>con igual geometría y versión de mapa?}
    D -- Sí --> D1[Devolver el análisis guardado] --> Z
    D -- No --> E{¿Hay uno pending o processing<br/>del mismo lote y especie?}
    E -- Sí --> E1[409 Conflict] --> Z
    E -- No --> F[Crear análisis 'pending' y encolar en Redis]
    F --> G[Responder 202]
    G --> P[Frontend consulta cada 2 s]

    F -.-> W1[Worker: estado 'processing']
    W1 --> W2[Recortar el GeoTIFF de la especie al polígono]
    W2 --> W3{¿Hay centros de píxel<br/>dentro del lote?}
    W3 -- No --> W4[Reintentar con los píxeles que toca el lote]
    W3 -- Sí --> W5
    W4 --> W5[Descartar NoData y valores negativos]
    W5 --> W6{¿Quedan píxeles válidos?}
    W6 -- No --> W7[Estado 'failed' + mensaje]
    W6 -- Sí --> W8[Calcular media, mín, máx, desvío y percentiles]
    W8 --> W9[Estado 'completed' + resultados]
    W7 --> P
    W9 --> P
    P --> Q([Mostrar tasa en kg MS/ha/día o el error])
```

## 6. Diagrama de estados del análisis

```mermaid
stateDiagram-v2
    [*] --> pending: POST /analyses
    pending --> processing: el worker toma la tarea
    processing --> completed: estadísticas calculadas
    processing --> failed: sin datos / fuera del mapa / error
    completed --> [*]
    failed --> [*]
```

## 7. Diagrama de clases (modelo de dominio)

```mermaid
classDiagram
    direction LR

    class User {
        +UUID id
        +str email
        +str hashed_password
        +str full_name
        +bool is_active
        +bool email_verified
        +str refresh_token_jti
        +int failed_login_attempts
        +datetime locked_until
        +datetime deleted_at
        +verify_password(password) bool
        +is_locked() bool
        +record_failed_login()
        +reset_failed_logins()
    }

    class Lot {
        +UUID id
        +UUID user_id
        +str name
        +float area_ha
        +Polygon geometry
        +datetime created_at
        +datetime updated_at
        +datetime deleted_at
    }

    class LotVersion {
        +UUID id
        +UUID lot_id
        +int version_number
        +str name
        +float area_ha
        +Polygon geometry
        +UUID changed_by
        +str change_reason
        +datetime created_at
    }

    class Analysis {
        +UUID id
        +UUID lot_id
        +ResourceType resource_type
        +float average_rate
        +float min_value
        +float max_value
        +float std_dev
        +dict percentiles
        +str raster_version
        +datetime raster_date
        +str lot_geometry_hash
        +AnalysisStatus status
        +str error_message
        +datetime analyzed_at
    }

    class AuditLog {
        +UUID id
        +str table_name
        +str record_id
        +str action
        +str old_values
        +str new_values
        +str user_id
        +datetime created_at
    }

    class ResourceType {
        <<enumeration>>
        RESOURCE_1 Alfalfa
        RESOURCE_2 Festuca
        RESOURCE_3 Raigrás
        RESOURCE_4 Pastizal natural
    }

    class AnalysisStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        FAILED
    }

    User "1" --> "0..*" Lot : es dueño de
    Lot "1" --> "1..*" LotVersion : historial
    User "1" --> "0..*" LotVersion : modifica
    Lot "1" --> "0..*" Analysis : tiene
    Analysis ..> ResourceType
    Analysis ..> AnalysisStatus
```

`AuditLog` está en el modelo pero todavía no se escribe (RN-AUD-03).

## 8. Diagrama de clases (servicios del backend)

```mermaid
classDiagram
    direction TB

    class AuthRouter {
        <<router /auth>>
        +register()
        +login()
        +refresh()
        +logout()
        +me()
    }
    class LotsRouter {
        <<router /lots>>
        +create()
        +list()
        +get()
        +versions()
        +update()
        +delete()
        +restore()
    }
    class AnalysesRouter {
        <<router /analyses>>
        +create()
        +check_cache()
        +list()
        +get()
        +timeseries()
    }
    class Security {
        <<core/security.py>>
        +hash_password()
        +create_access_token()
        +create_refresh_token(jti)
        +decode_token()
    }
    class LotService {
        <<services/lot_service.py>>
        +validate_geometry()
        +calculate_area_ha()
        +validate_area()
        +ensure_unique_name()
        +create_lot()
        +update_lot()
        +delete_lot()
        +restore_lot()
        +create_lot_version()
    }
    class RasterService {
        <<services/raster_service.py>>
        +clip_raster_to_geometry()
        +calculate_statistics()
        +analyze_lot_resource()
        +run_analysis_task()
        +get_time_series()
    }
    class RasterCatalog {
        <<core/raster_config.py>>
        +RASTER_CATALOG
        +get_raster_path()
        +get_raster_version()
    }
    class AnalysisWorker {
        <<Celery task>>
        +run_analysis_task(analysis_id)
    }

    AuthRouter --> Security
    LotsRouter --> LotService
    AnalysesRouter --> RasterService
    AnalysesRouter ..> AnalysisWorker : encola
    AnalysisWorker --> RasterService
    RasterService --> RasterCatalog
```
