// VectorLayer.tsx - Capa GeoJSON con estilos y popups
import React from "react"
import L, { GeoJSON, FeatureGroup } from "leaflet"
import { useGeoJSON } from "@/hooks/useGeoJSON"

export interface VectorLayerProps {
  geojson: GeoJSON.FeatureCollection | null
  style?: (feature: GeoJSON.Feature) => L.PathOptions
  onEachFeature?: (feature: GeoJSON.Feature, layer: L.Layer) => void
  layerId?: string
}

export const VectorLayer = ({
  geojson,
  style,
  onEachFeature,
  layerId,
}: VectorLayerProps) => {
  const { addGeoJSON, removeLayer } = useMap()

  // Usar hook useGeoJSON para styling
  const geoJSONProps = useGeoJSON({
    geojson,
    style,
    onEachFeature,
  })

  useEffect(() => {
    if (geojson) {
      addGeoJSON(geojson, layerId!)
    }
    return () => {
      removeLayer(layerId!)
    }
  }, [geojson, layerId])

  return null
}