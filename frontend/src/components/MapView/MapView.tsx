// MapView.tsx - Componente solo lectura para visualizar lotes en mapa
import React from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { useMap } from "./useMap"
import { BaseLayers } from "./BaseLayers"
import { VectorLayer } from "./VectorLayer"
import { useGeoJSON } from "@/hooks/useGeoJSON"

export interface MapViewProps {
  lot: {
    id: string
    name: string
    area_ha: number
    geometry: GeoJSON.Feature | null
    created_at: string
  }
  showPopup?: boolean
}

export const MapView = ({ lot, showPopup = true }: MapViewProps) => {
  const {
    mapRef,
    fitToLayer,
    getMap,
  } = useMap()

  // Cuando la geometría del lote cambie, actualizar el mapa
  useEffect(() => {
    if (lot.geometry) {
      const geojson: {
        type: string
        features: Array<{
          type: string
          properties: any
          geometry: {
            type: string
            coordinates: number[][]
          }
        }>
      } = {
        type: "FeatureCollection",
        features: [lot.geometry],
      }
      // Agregar al mapa usando hook interno
      const vectorLayerRef = { current: null }
      // Renderizar vía useGeoJSON hook
      useGeoJSON({
        geojson: {
          type: "FeatureCollection",
          features: lot.geometry
            ? [{ type: "Feature", properties: {}, geometry: lot.geometry.geometry }]
            : [],
        },
        onEachFeature: (feature, layer) => {
          if (showPopup && lot.name) {
            const area = lot.area_ha ? `${lot.area_ha.toFixed(2)} ha` : ""
            layer.bindPopup(
              `<b>${lot.name}</b><br/>Área: ${area}<br/>Creado: ${lot.created_at}`
            )
          }
        },
      })
      fitToLayer("view-lot")
    }
  }, [lot.geometry, lot.name, lot.area_ha, lot.created_at, showPopup])

  return (
    <div className="map-view-wrapper">
      <div
        className="map-view-container"
        style={{ height: "500px", width: "100%" }}
        ref={mapRef}
      >
        <BaseLayers
          selectedLayer="openstreetmap"
          onLayerChange={() => {}}
        />

        <VectorLayer
          geojson={{ type: "FeatureCollection", features: [] }}
          layerId="view-lot"
        />

        {/* Mostrar lote específico */}
        {lot.geometry && (
          <VectorLayer
            geojson={{
              type: "FeatureCollection",
              features: [
                {
                  type: "Feature",
                  properties: {
                    id: lot.id,
                    name: lot.name,
                  },
                  geometry: {
                    type: lot.geometry.geometry.type,
                    coordinates: lot.geometry.geometry.coordinates,
                  },
                },
              ],
            }}
            style={({
              feature,
            }) => ({
              color: "#ff6600",
              weight: 3,
              fillColor: "#ff9966",
              fillOpacity: 0.6,
            })}
          />
        )}
      </div>
    </div>
  )
}