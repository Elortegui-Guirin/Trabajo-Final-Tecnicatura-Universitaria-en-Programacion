// MapEditor.tsx - Componente mapa interactivo con Leaflet + leaflet.pm
import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, GeoJSON, Map } from 'react-leaflet'
import 'leaflet.pm/dist/leaflet.pm.css'
import 'leaflet.pm'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import 'leaflet.pm'

// Fix para iconos por defecto en Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

interface MapEditorProps {
  initialGeometry?: GeoJSON.Feature<GeoJSON.Polygon> | null
  onGeometryChange: (geojson: GeoJSON.Feature<GeoJSON.Polygon>) => void
  readOnly?: boolean
  height?: string
}

export function MapEditor({ 
  initialGeometry, 
  onGeometryChange, 
  readOnly = false,
  height = '400px'
}: MapEditorProps) {
  const mapRef = useRef<Map | null>(null)
  const drawLayerRef = useRef<L.LayerGroup | null>(null)
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null)

  // Inicializar controles de dibujo
  useEffect(() => {
    if (!mapInstance || readOnly) return

    const drawLayer = new L.LayerGroup()
    drawLayer.addTo(mapInstance)
    drawLayerRef.current = drawLayer

    // Cargar geometría inicial si existe
    if (initialGeometry) {
      const geoJsonLayer = L.geoJSON(initialGeometry)
      geoJsonLayer.addTo(drawLayer)
      mapInstance.fitBounds(geoJsonLayer.getBounds())
    }

    // Habilitar controles de dibujo/edición
    mapInstance.pm.addControls({
      position: 'topleft',
      drawMarker: false,
      drawPolyline: false,
      drawRectangle: false,
      drawCircle: false,
      drawPolygon: true,
      editMode: true,
      removalMode: true,
      cutPolygon: true,
      oneBlock: true,
    })

    // Evento: crear polígono
    mapInstance.on('pm:create', (e: any) => {
      const geojson = e.layer.toGeoJSON() as GeoJSON.Feature<GeoJSON.Polygon>
      drawLayer.clearLayers()
      drawLayer.addLayer(e.layer)
      onGeometryChange(geojson)
    })

    // Evento: editar polígono
    mapInstance.on('pm:edit', (e: any) => {
      const layers = e.layers
      layers.eachLayer((layer: any) => {
        const geojson = layer.toGeoJSON() as GeoJSON.Feature<GeoJSON.Polygon>
        onGeometryChange(geojson)
      })
    })

    // Evento: eliminar
    mapInstance.on('pm:remove', () => {
      drawLayer.clearLayers()
      onGeometryChange({
        type: 'Feature',
        properties: {},
        geometry: { type: 'Polygon', coordinates: [] }
      } as GeoJSON.Feature<GeoJSON.Polygon>)
    })

    return () => {
      mapInstance.pm.removeControls()
      drawLayer.remove()
    }
  }, [mapInstance, initialGeometry, readOnly, onGeometryChange])

  // Calcular área client-side para feedback
  const calculateAreaHa = (geojson: GeoJSON.Feature<GeoJSON.Polygon>): number => {
    try {
      const coords = geojson.geometry.coordinates[0]
      if (!coords || coords.length < 4) return 0
      
      // Shoelace formula para área aproximada en grados², luego convertir
      let area = 0
      for (let i = 0; i < coords.length - 1; i++) {
        area += coords[i][0] * coords[i + 1][1] - coords[i + 1][0] * coords[i][1]
      }
      area = Math.abs(area) / 2
      
      // Aproximación rough: 1 grado² ≈ 12300 km² en latitud media
      // Para feedback visual only, server valida definitivo
      return Math.round(area * 12300 * 100) / 100
    } catch {
      return 0
    }
  }

  const areaHa = initialGeometry ? calculateAreaHa(initialGeometry) : 0

  return (
    <div style={{ height, width: '100%' }} className="rounded-xl border border-gray-200 overflow-hidden">
      <MapContainer
        center={[-34.6, -58.4]}
        zoom={10}
        scrollWheelZoom={true}
        whenCreated={setMapInstance}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Tiles &copy; Esri"
        />
        
        {initialGeometry && (
          <GeoJSON
            data={initialGeometry}
            style={() => ({
              color: '#16a34a',
              weight: 2,
              fillColor: '#22c55e',
              fillOpacity: 0.3,
            })}
          />
        )}
      </MapContainer>
      
      {areaHa > 0 && (
        <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur px-3 py-1.5 rounded-lg shadow-lg text-sm font-medium text-gray-800">
          Área aprox: {areaHa.toFixed(2)} ha
        </div>
      )}
    </div>
  )
}

// Tipos GeoJSON locales para evitar import circular
namespace GeoJSON {
  export interface Polygon {
    type: 'Polygon'
    coordinates: number[][][]
  }
  export interface Feature<G> {
    type: 'Feature'
    properties: Record<string, any>
    geometry: G
  }
}