// DrawControl.tsx - Toolbar de dibujo con leaflet.pm
import React, { useEffect, useRef } from "react"
import L, { use, pm } from "leaflet"
import "leaflet.pm/dist/leaflet.pm.css"
import { simplifyGeometry, getVertexCount, MAX_VERTICES } from "@/hooks/useGeoJSON"

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
  const mapRef = useRef<L.Map | null>(null)
  const vertexCountRef = useRef(0)

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
      // Capturar referencia al mapa desde el DrawControl global
      const map = (window as any).mapRef?.current
      
      if (map) {
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
          snappable: true,
          snapDistance: 20,
          cursorMarker: true,
        }).addTo(map)

        // Eventos de dibujo
        // @ts-ignore - eventos de leaflet.pm
        L.PM.events.draw("Polygon", (e: any) => {
          const geojson = e.layer.toGeoJSON()
          const vertexCount = getVertexCount(geojson)
          vertexCountRef.current = vertexCount
          
          // Advertir si se acerca al límite
          if (vertexCount > 4000) {
            console.warn(`Geometría con ${vertexCount} vértices (máx. ${MAX_VERTICES})`)
          }
          
          onDrawEnd(geojson)
        })

        // Eventos de edición
        // @ts-ignore
        L.PM.events.edit((e: any) => {
          if (e.type === "editend") {
            const geojson = e.layer.toGeoJSON()
            const vertexCount = getVertexCount(geojson)
            vertexCountRef.current = vertexCount
            
            if (vertexCount > 4000) {
              console.warn(`Geometría editada con ${vertexCount} vértices (máx. ${MAX_VERTICES})`)
            }
            
            onEditEnd(geojson)
          }
        })

        // Eventos de remoción
        // @ts-ignore
        L.PM.events.remove((e: any) => {
          onRemove()
        })
      }
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

// Referencia global al mapa para el DrawControl (hack temporal)
// En producción, usar Context o estado compartido
if (typeof window !== "undefined") {
  (window as any).mapRef = (window as any).mapRef || { current: null }
}