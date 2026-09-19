// DrawControl.tsx - Toolbar de dibujo con leaflet.pm
import React, { useEffect, useRef } from "react"
import L, { use, pm } from "leaflet"
import "leaflet.pm/dist/leaflet.pm.css"

// Desactivar temporalmente pm hasta que Leaflet 1.9+ esté confirmado
// import "leaflet.pm/dist/leaflet.pm.js"

// Extensiones para pm types
declare global {
  interface L {
    pm: any
  }
}

export const DrawControl = ({
  onDrawEnd,
  onEditEnd,
  onRemove,
  drawnItemsRef,
}: {
  onDrawEnd: (geojson: any) => void
  onEditEnd: (geojson: any) => void
  onRemove: () => void
  drawnItemsRef?: React.RefObject<L.FeatureGroup | null>
}) => {
  useEffect(() => {
    // Inicializar drawn items group
    const drawnItems = L.featureGroup()
    if (drawnItemsRef?.current) {
      drawnItemsRef.current.addLayer(drawnItems)
    }

    // Agregar controles de draw
    // NOTA: leaflet.pm requiere Leaflet 1.7.x compatible
    // En producción verificar compatibilidad con la versión de Leaflet instalada
    try {
      L.pm.addControls({
        position: "topleft",
        drawMarker: false,
        drawPolyline: false,
        drawRectangle: false,
        drawCircle: false,
        drawPolygon: true,
        editMode: true,
        removalMode: true,
        cutPolygon: true,
      }).addTo(mapRef.current!)

      // Eventos de dibujo
      // @ts-ignore - eventos de leaflet.pm
      L.PM.events.draw("Polygon", (e: any) => {
        const geojson = e.layer.toGeoJSON()
        onDrawEnd(geojson)
      })

      // Eventos de edición
      // @ts-ignore
      L.PM.events.edit((e: any) => {
        if (e.type === "editend") {
          const geojson = e.layer.toGeoJSON()
          onEditEnd(geojson)
        }
      })

      // Eventos de remoción
      // @ts-ignore
      L.PM.events.remove((e: any) => {
        onRemove()
      })
    } catch (err) {
      console.warn("leaflet.pm no disponible, usando drawing control nativo")
    }

    return () => {
      // Cleanup
      if (drawnItemsRef?.current) {
        drawnItemsRef.current.removeLayer(drawnItems)
      }
    }
  }, [onDrawEnd, onEditEnd, onRemove])

  return null
}

// Referencia al mapa para el hook
const mapRef = { current: null }
export { mapRef }