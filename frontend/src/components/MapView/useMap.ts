// useMap.ts - Hook para lógica de mapa Leaflet
import { useRef, useEffect } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { useGeoJSON } from "@/hooks/useGeoJSON"

// Tipos
export interface UseMapReturn {
  mapRef: React.RefObject<L.Map | null>
  addGeoJSON: (geojson: GeoJSON.FeatureCollection, layerId: string, style?: L.PathOptions) => void
  removeLayer: (layerId: string) => void
  fitToLayer: (layerId: string, padding?: number) => void
  getMap: () => L.Map | null
}

// Capa base options
export type BaseLayerType =
  | "openstreetmap"
  | "cartoDB_voyager"
  | "esri_world imagery"

// URLs de capas base
const BASE_LAYERS = {
  openstreetmap: {
    name: "OpenStreetMap",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    subdomains: ["a", "b", "c"],
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  cartoDB_voyager: {
    name: "CartoDB Voyager",
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
    subdomains: ["a", "b", "c"],
    attribution:
      '&copy; <a href="https://www.carto.com/attributions">CartoDB</a> contributors',
  },
  esri_world_imagery: {
    name: "Esri World Imagery",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/{z}/{x}/{y}.png",
    subdomains: ["", "a", "b", "c"],
    attribution:
      '&copy; <a href="https://www.esri.com">Esri</a> contributors',
  },
}

export const useMap = (): UseMapReturn => {
  const mapRef = useRef<L.Map | null>(null)
  const layerIdCounter = 0 // Simplificado: en producción usar un store/counter real

  // Inicializar mapa cuando el ref cambia
  useEffect(() => {
    if (mapRef.current) return
    const map = L.map(mapRef.current!)
    // Add base layer
    L.tileLayer(BASE_LAYERS.openstreetmap.url, {
      attribution: BASE_LAYERS.openstreetmap.attribution,
      maxZoom: 19,
      subdomains: BASE_LAYERS.openstreetmap.subdomains,
    }).addTo(map)

    // Add default base layers control
    const baseLayers = {
      "OpenStreetMap": L.tileLayer(BASE_LAYERS.openstreetmap.url, {
        attribution: BASE_LAYERS.openstreetmap.attribution,
        maxZoom: 19,
        subdomains: BASE_LAYERS.openstreetmap.subdomains,
      }),
      "CartoDB Voyager": L.tileLayer(BASE_LAYERS.cartoDB_voyager.url, {
        attribution: BASE_LAYERS.cartoDB_voyager.attribution,
        maxZoom: 19,
        subdomains: BASE_LAYERS.cartoDB_voyager.subdomains,
      }),
      "Esri World Imagery": L.tileLayer(BASE_LAYERS.esri_world_imagery.url, {
        attribution: BASE_LAYERS.esri_world_imagery.attribution,
        maxZoom: 19,
        subdomains: BASE_LAYERS.esri_world_imagery.subdomains,
      }),
    }

    L.control.layers(baseLayers).addTo(map)
    mapRef.current = map
  }, [])

  const addGeoJSON = (geojson: GeoJSON.FeatureCollection, layerId: string, style?: L.PathOptions) => {
    if (!mapRef.current) return
    // Remover capa existente con mismo layerId si existe
    removeLayer(layerId)
    
    const pathOptions: L.PathOptions = style || {
      color: "#3388ff",
      weight: 2,
      fillColor: "#66b2ff",
      fillOpacity: 0.4,
    }

    L.geoJSON(geojson, { style }).addTo(mapRef.current!)
  }

  const removeLayer = (layerId: string) => {
    if (!mapRef.current) return
    // En una implementación completa, rastrearíamos las capas por layerId
    // Por ahora removemos la última capa de GeoJSON añadida
    const layers = mapRef.current!.eachLayer((layer) => {
      if (layer instanceof L.GeoJSON) {
        mapRef.current!.removeLayer(layer)
      }
    })
  }

  const fitToLayer = (layerId: string, padding: number = 20) => {
    if (!mapRef.current) return
    const layers = mapRef.current!.eachLayer((layer) => {
      if (layer instanceof L.GeoJSON) {
        mapRef.current!.fitBounds(layer.getBounds(), { padding: padding })
      }
    })
  }

  const getMap = () => mapRef.current

  return {
    mapRef,
    addGeoJSON,
    removeLayer,
    fitToLayer,
    getMap,
  }
}