// MapEditor.tsx - Componente alto nivel: mapa con draw/editar/eliminar
import React, { useStateBoard does check `user.is_active` and the type is "access". The main issues might be:
1. The auth router wasn't being included in main.js (which I already fixed)
2. The user might needUseEffect, useRef, useState } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { useMap } from "./useMap"
import { BaseLayers } from "./BaseLayers"
import { DrawControl } from "./DrawControl"
import { VectorLayer } from "./VectorLayer"
import { GeoJSON } from "geojson"

// Interfaz de retorno del hook
interface MapEditorProps {
  initialGeometry?: GeoJSON.Feature | null
  onGeometryChange: (geojson: GeoJSON.Feature | null) => void
  readOnly?: boolean
  height: string
}

export const MapEditor = ({
  initialGeometry,
  onGeometryChange,
  readOnly = false,
  height,
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

  // Emitir cambio de geometría cuando el usuario termine de dibujar/editar
  // Esto se conecta con el DrawControl events
  const handleDrawEnd = (geojson: any) => {
    const feature = geojson as GeoJSON.Feature
    // Validar que sea polígono válido
    if (feature.geometry.type === "Polygon" && feature.geometry.coordinates?.[0]?.length >= 4) {
      setSelectedGeometry(feature)
      onGeometryChange(feature)
    }
  }

  const handleEditEnd = (geojson: any) => {
    const feature = geojson as GeoJSON.Feature
    if (feature.geometry.type === "Polygon") {
      setSelectedGeometry(feature)
      onGeometryChange(feature)
    }
  }

  const handleRemove = () => {
    setSelectedGeometry(null)
    onGeometryChange(null)
  }

  if (!mapRef.current) {
    return null // Mapa aún no inicializado
  }

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
              color: "#3388ff",
              weight: 2,
              fillColor: "#!,
              fillOpacity: 0.4,
            })}
          />
        })
      </div>

      {/* Botón de cerrar/limpiar modo edición (solo modo no readOnly) */}
      {!readOnly && (
        <button
          className="map-editor-close"
          onClick={() => {
            setSelectedGeometry(null)
            onGeometryChange(null)
          }}
          title="Limpiar geometría"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path d="M3 6l8 8L3 6" />
            <path d="M3 12L3 12M12 3l9 9M9 9l9 9" />
          </svg>
        </button>
      )}
    </div>
  )
}

// Estilos inline para el componente
const useStyles = () => {
  // Los estilos se aplican via className en el JSX
}