// MapEditor.tsx - Componente alto nivel: mapa con draw/editar/eliminar
import React, { useEffect, useRef, useState } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { useMap } from "./useMap"
import { BaseLayers } from "./BaseLayers"
import { DrawControl } from "./DrawControl"
import { VectorLayer } from "./VectorLayer"
import { GeoJSON } from "geojson"
import { validatePolygon, getVertexCount, calculateAreaHa, simplifyGeometry, MAX_VERTICES } from "@/hooks/useGeoJSON"

// Fix para iconos por defecto en Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Interfaz de retorno del hook
interface MapEditorProps {
  initialGeometry?: GeoJSON.Feature | null
  onGeometryChange: (geojson: GeoJSON.Feature | null) => void
  readOnly?: boolean
  height: string
  showVertexCount?: boolean
  showArea?: boolean
}

export const MapEditor = ({
  initialGeometry,
  onGeometryChange,
  readOnly = false,
  height,
  showVertexCount = true,
  showArea = true,
}: MapEditorProps) => {
  const {
    mapRef,
    addGeoJSON,
    removeLayer,
    fitToLayer,
    getMap,
  } = useMap()

  const [drawing, setDrawing] = useState(false)
  const [selectedGeometry, setSelectedGeometry] = useState<
    GeoJSON.Feature | null
  >(initialGeometry ?? null)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [validationWarnings, setValidationWarnings] = useState<string[]>([])
  const [vertexCount, setVertexCount] = useState<number>(0)
  const [areaHa, setAreaHa] = useState<number | null>(null)

  // Cuando cambie la geometría seleccionada, notificar al padre y al mapa
  useEffect(() => {
    if (selectedGeometry) {
      setDrawing(true)
      // Agregar geometría al mapa como capa vectorial
      const geojson: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: [selectedGeometry],
      }
      addGeoJSON(geojson, "current-draw")
      fitToLayer("current-draw")
    } else {
      setDrawing(false)
      removeLayer("current-draw")
    }
  }, [selectedGeometry])

  // Validar geometría cuando cambie
  useEffect(() => {
    if (selectedGeometry) {
      const result = validatePolygon(selectedGeometry)
      setValidationErrors(result.errors)
      setValidationWarnings(result.warnings)
      setVertexCount(result.vertexCount)
      setAreaHa(result.areaHa)
    } else {
      setValidationErrors([])
      setValidationWarnings([])
      setVertexCount(0)
      setAreaHa(null)
    }
  }, [selectedGeometry])

  // Emitir cambio de geometría cuando el usuario termine de dibujar/editar
  // Esto se conecta con el DrawControl events
  const handleDrawEnd = (geojson: any) => {
    const feature = geojson as GeoJSON.Feature
    // Validar que sea polígono válido
    if (feature.geometry.type === "Polygon" && feature.geometry.coordinates?.[0]?.length >= 4) {
      // Validar antes de aceptar
      const result = validatePolygon(feature)
      if (!result.valid) {
        // Errores de validación: no aceptar, solo mostrar errores
        return
      }
      
      // Simplificar si es necesario
      const simplified = simplifyGeometry(feature, 0.00001)
      if (simplified !== feature) {
        // Se simplificó - avisar al usuario
        console.warn("Geometría simplificada automáticamente")
      }
      
      setSelectedGeometry(simplified)
      onGeometryChange(simplified)
    }
  }

  const handleEditEnd = (geojson: any) => {
    const feature = geojson as GeoJSON.Feature
    if (feature.geometry.type === "Polygon") {
      const result = validatePolygon(feature)
      if (!result.valid) {
        // Rechazar edición inválida - el componente DrawControl debería manejar esto
        // Pero por seguridad, validamos aquí también
        return
      }
      
      const simplified = simplifyGeometry(feature, 0.00001)
      setSelectedGeometry(simplified)
      onGeometryChange(simplified)
    }
  }

  const handleRemove = () => {
    setSelectedGeometry(null)
    onGeometryChange(null)
  }

  if (!mapRef.current) {
    return null // Mapa aún no inicializado
  }

  const hasErrors = validationErrors.length > 0

  return (
    <div className="map-editor-wrapper">
      <div
        className="map-container"
        style={{ height: height, width: "100%" }}
        ref={mapRef}
      >
        {/* Capas base */}
        <BaseLayers
          selectedLayer="openstreetmap"
          onLayerChange={() => {}}
        />

        {/* Capas vectoriales (lotes dibujados) */}
        <VectorLayer
          geojson={{ type: "FeatureCollection", features: [] }}
          layerId="drawn-lots"
        />

        {/* Control de dibujo - solo modo no readOnly */}
        {!readOnly && (
          <DrawControl
            onDrawEnd={handleDrawEnd}
            onEditEnd={handleEditEnd}
            onRemove={handleRemove}
            drawnItemsRef={mapRef}
          />
        )}

        {/* Layer de geometría actual */}
        {selectedGeometry && (
          <VectorLayer
            geojson={{ type: "FeatureCollection", features: [selectedGeometry] }}
            style={({
              feature,
            }) => ({
              color: hasErrors ? "#dc2626" : "#3388ff",
              weight: 2,
              fillColor: hasErrors ? "#fca5a5" : "#22c55e",
              fillOpacity: 0.4,
            })}
          />
        )}
      </div>

      {/* Panel de información y validación */}
      {!readOnly && (
        <div className={`map-editor-info ${hasErrors ? 'has-errors' : ''}`}>
          <div className="info-header">
            <span className="info-title">Información del lote</span>
            {!readOnly && (
              <button
                className="map-editor-close"
                onClick={() => {
                  setSelectedGeometry(null)
                  onGeometryChange(null)
                }}
                title="Limpiar geometría"
                aria-label="Limpiar geometría"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Área */}
          {showArea && areaHa !== null && (
            <div className="info-row">
              <span className="info-label">Área:</span>
              <span className={`info-value ${areaHa !== null && areaHa < 0.01 ? 'error' : ''}`}>
                {areaHa.toFixed(4)} ha
                {areaHa !== null && areaHa < 0.01 && (
                  <span className="error-badge">Mín: 0.01 ha</span>
                )}
              </span>
            </div>
          )}

          {/* Vértices */}
          {showVertexCount && (
            <div className="info-row">
              <span className="info-label">Vértices:</span>
              <span className={`info-value ${vertexCount > 5000 ? 'error' : vertexCount > 4000 ? 'warning' : ''}`}>
                {vertexCount.toLocaleString()} / {MAX_VERTICES.toLocaleString()}
                {vertexCount > MAX_VERTICES && <span className="error-badge">Excede límite</span>}
                {vertexCount > 4000 && vertexCount <= MAX_VERTICES && <span className="warning-badge">Cerca del límite</span>}
              </span>
            </div>
          )}

          {/* Errores */}
          {validationErrors.length > 0 && (
            <div className="validation-errors">
              {validationErrors.map((error, i) => (
                <div key={i} className="error-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                  <span>{error}</span>
                </div>
              ))}
            </div>
          )}

          {/* Advertencias */}
          {validationWarnings.length > 0 && (
            <div className="validation-warnings">
              {validationWarnings.map((warning, i) => (
                <div key={i} className="warning-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <span>{warning}</span>
                </div>
              ))}
            </div>
          )}

          {/* Botón limpiar (solo modo no readOnly) */}
          {!readOnly && (
            <button
              className="map-editor-close"
              onClick={() => {
                setSelectedGeometry(null)
                onGeometryChange(null)
              }}
              title="Limpiar geometría"
              aria-label="Limpiar geometría"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          )}
        </div>
      )}

      {/* Leyenda de capas base (solo readOnly) */}
      {readOnly && (
        <div className="map-editor-info read-only">
          <span className="info-title">Mapa de referencia</span>
          <span className="info-label">Modo solo lectura - Use las capas base para navegación</span>
        </div>
      )}
    </div>
  )
}

// Estilos CSS inline usando className
// Los estilos se definen en map.css