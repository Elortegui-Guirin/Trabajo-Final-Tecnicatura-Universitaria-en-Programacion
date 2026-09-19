// BaseLayers.tsx - Controles de capas base para Leaflet
import React from "react"
import L, { tileLayer, LayersControl, attribution } from "leaflet"
import "leaflet/dist/leaflet.css"

// Definición de capas base
export type BaseLayerType = "openstreetmap" | "cartoDB_voyager" | "esri_world_imagery"

const baseLayers: Record<BaseLayerType, {
  layer: ReturnType<typeof tileLayer>
  name: string
}> = {
  openstreetmap: {
    layer: tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }),
    name: "OpenStreetMap",
  },
  cartoDB_voyager: {
    layer: tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.carto.com/attributions">CartoDB</a> contributors',
      maxZoom: 19,
    }),
    name: "CartoDB Voyager",
  },
  esri_world_imagery: {
    layer: tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.esri.com">Esri</a> contributors',
      maxZoom: 19,
    }),
    name: "Esri World Imagery",
  },
}

export const BaseLayers = ({
  selectedLayer = "openstreetmap",
  onLayerChange,
}: {
  selectedLayer?: BaseLayerType
  onLayerChange?: (layer: BaseLayerType) => void
}) => {
  return (
    <div className="leaflet-control leaflet-control-layers leaflet-control-layers-expanded">
      {Object.entries(baseLayers).map(([key, { layer, name }]) => (
        <label key={key} className="leaflet-control-item">
          <input
            type="radio"
            checked={selectedLayer === key}
            onChange={() => onLayerChange?.(key)}
            name="base-layer"
            className="leaflet-control-input leaflet-radio"
          />
          <span>{name}</span>
        </label>
      ))}
    </div>
  )
}