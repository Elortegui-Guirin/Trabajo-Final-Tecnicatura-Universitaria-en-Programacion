# Trabajo-Final-Tecnicatura-Universitaria-en-Programacion
Repositorio que reúne el Trabajo Final Tecnicatura Universitaria en Programación

# GeoForraje 1.0

> Plataforma web para la gestión de lotes agropecuarios georreferenciados y análisis de crecimiento forrajero mediante capas raster.

---

## 📋 Descripción

**GeoForraje 1.0** es una aplicación web diseñada para productores y técnicos agropecuarios que permite:

- Registrar y administrar lotes dibujados sobre un mapa interactivo.
- Almacenar lotes en una base de datos geoespacial (PostGIS).
- Consultar indicadores de crecimiento de recursos forrajeros a partir de capas raster previamente procesadas.
- Obtener estadísticas como la tasa promedio de crecimiento dentro de un lote seleccionado.

El sistema facilita la toma de decisiones basada en datos espaciales, optimizando el manejo de recursos forrajeros.

---

## Objetivo General

Desarrollar una aplicación web que permita gestionar lotes georreferenciados y calcular indicadores productivos a partir de capas raster de recursos forrajeros.

---

## Alcance del MVP (Versión 1.0)

### Gestión de Usuarios
- Registro de usuarios.
- Inicio de sesión.
- Autenticación mediante JWT.

### Gestión de Lotes
- Crear, editar, eliminar y consultar lotes guardados.

### Visualización Geográfica
- Mapa interactivo con Leaflet.
- Dibujo de polígonos sobre el mapa.
- Visualización de lotes registrados.

### Análisis Forrajero
- Selección de uno de **cuatro recursos forrajeros** disponibles.
- Consulta de la capa raster correspondiente.
- Cálculo de la **tasa promedio de crecimiento** dentro del lote.
- Visualización del resultado obtenido.

---

## Tecnologías utilizadas

### Frontend
- React
- TypeScript
- React Router
- Zustand (manejo de estado)
- TanStack Query (fetching y caché)
- Tailwind CSS
- Leaflet (mapas interactivos)

### Backend
- Python
- FastAPI
- Pydantic
- SQLModel

### Base de Datos
- PostgreSQL
- PostGIS (extensión espacial)

### Procesamiento Geoespacial
- Rasterio
- GeoJSON

### Seguridad
- JWT (JSON Web Tokens)

### Despliegue
- Vercel (Frontend)
- Render (Backend)

---

## Evolución futura (fuera del alcance v1.0)

- Series temporales de crecimiento.
- Gráficos históricos.
- Comparación entre campañas.
- Actualización automática de capas raster.
- Integración con Google Earth Engine.
- Generación de alertas productivas.

---

## Integrantes del equipo

- Verónica Guirin  
- María del Rosario Margarita Iturralde Elortegui  

**Tutor:** Gerardo Adrián Herrera

---

## Estructura del proyecto (sugerida)

