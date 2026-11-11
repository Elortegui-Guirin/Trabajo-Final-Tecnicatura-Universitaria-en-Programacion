// MapEditor.tsx - Mapa para dibujar / editar / ver el polígono de un lote
// react-leaflet (MapContainer) + Geoman (@geoman-io/leaflet-geoman-free) para dibujar.
import { useEffect, useRef, useState } from "react"
import L from "leaflet"
import { MapContainer, TileLayer, LayersControl, useMap } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import "@geoman-io/leaflet-geoman-free"
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css"
import type { Feature } from "geojson"
import { validatePolygon, simplifyGeometry, MAX_VERTICES } from "@/hooks/useGeoJSON"

// Centro por defecto: provincia de Buenos Aires (zona cubierta por los mapas de crecimiento)
const DEFAULT_CENTER: [number, number] = [-37.0, -60.0]
const DEFAULT_ZOOM = 7

const POLYGON_STYLE = { color: "#15803d", weight: 2, fillColor: "#22c55e", fillOpacity: 0.35 }

interface MapEditorProps {
  initialGeometry?: Feature | null
  onGeometryChange: (geojson: Feature | null) => void
  readOnly?: boolean
  height: string
  showVertexCount?: boolean
  showArea?: boolean
}

/**
 * Capa del lote + controles de dibujo. Va dentro de <MapContainer> para usar useMap().
 * Se mantiene un solo polígono: dibujar uno nuevo reemplaza al anterior.
 */
function LotLayer({
  initialGeometry,
  readOnly,
  onChange,
}: {
  initialGeometry?: Feature | null
  readOnly: boolean
  onChange: (feature: Feature | null) => void
}) {
  const map = useMap()
  const layerRef = useRef<L.Layer | null>(null)
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  // Avisar cambios del polígono (editar vértices o moverlo)
  const watchLayer = (layer: L.Layer) => {
    const emit = () => onChangeRef.current((layer as L.Polygon).toGeoJSON() as Feature)
    layer.on("pm:edit", emit)
    layer.on("pm:dragend", emit)
  }

  // Geometría inicial (lote existente): se dibuja una sola vez, cuando todavía no hay polígono.
  // No se vuelve a dibujar cuando el formulario recibe la geometría que el usuario acaba de trazar.
  useEffect(() => {
    if (!initialGeometry?.geometry || layerRef.current) return
    const layer = L.geoJSON(initialGeometry as any, { style: POLYGON_STYLE }).getLayers()[0]
    if (!layer) return
    layer.addTo(map)
    layerRef.current = layer
    map.fitBounds((layer as L.Polygon).getBounds(), { padding: [30, 30], maxZoom: 16 })
    if (!readOnly) watchLayer(layer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, readOnly, JSON.stringify(initialGeometry?.geometry ?? null)])

  // Al desmontar, sacar el polígono del mapa
  useEffect(() => () => {
    layerRef.current?.remove()
    layerRef.current = null
  }, [map])

  // Controles de dibujo (solo en modo edición)
  useEffect(() => {
    if (readOnly) return
    const pm = (map as any).pm
    if (!pm) {
      console.error("Geoman no está cargado: no se puede dibujar")
      return
    }

    pm.setLang("es")
    pm.addControls({
      position: "topleft",
      drawMarker: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: true,
      drawPolygon: true,
      drawCircle: false,
      drawText: false,
      editMode: true,
      dragMode: true,
      cutPolygon: false,
      removalMode: true,
      rotateMode: false,
    })
    pm.setGlobalOptions({ pathOptions: POLYGON_STYLE, snappable: true, snapDistance: 15 })

    const handleCreate = (e: any) => {
      // Un solo lote: si ya había un polígono, se reemplaza
      if (layerRef.current && layerRef.current !== e.layer) layerRef.current.remove()
      layerRef.current = e.layer
      watchLayer(e.layer)
      onChangeRef.current(e.layer.toGeoJSON() as Feature)
    }
    const handleRemove = (e: any) => {
      if (e.layer === layerRef.current) {
        layerRef.current = null
        onChangeRef.current(null)
      }
    }
    map.on("pm:create", handleCreate)
    map.on("pm:remove", handleRemove)

    return () => {
      map.off("pm:create", handleCreate)
      map.off("pm:remove", handleRemove)
      pm.removeControls()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, readOnly])

  return null
}

export const MapEditor = ({
  initialGeometry,
  onGeometryChange,
  readOnly = false,
  height,
  showVertexCount = true,
  showArea = true,
}: MapEditorProps) => {
  const [current, setCurrent] = useState<Feature | null>(initialGeometry ?? null)

  // Si llega una geometría desde afuera (lote existente), mostrarla.
  // Si el formulario la pone en null (polígono inválido), se mantiene la actual para seguir viendo los errores.
  useEffect(() => {
    if (initialGeometry) setCurrent(initialGeometry)
  }, [JSON.stringify(initialGeometry?.geometry ?? null)]) // eslint-disable-line react-hooks/exhaustive-deps

  const validation = current ? validatePolygon(current) : null

  const handleChange = (feature: Feature | null) => {
    if (!feature) {
      setCurrent(null)
      onGeometryChange(null)
      return
    }
    const simplified = simplifyGeometry(feature) as Feature
    setCurrent(simplified)
    // Solo se informa al formulario si el polígono es válido
    onGeometryChange(validatePolygon(simplified).valid ? simplified : null)
  }

  return (
    <div className="map-editor-wrapper">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        style={{ height, width: "100%", borderRadius: "0.5rem" }}
        scrollWheelZoom
      >
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satélite (Esri)">
            <TileLayer
              attribution="&copy; Esri"
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              maxZoom={19}
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        <LotLayer initialGeometry={initialGeometry} readOnly={readOnly} onChange={handleChange} />
      </MapContainer>

      {!readOnly && (
        <div className="mt-2 rounded-lg border border-gray-200 bg-white p-3 text-sm">
          {!current && (
            <p className="text-gray-500">
              Usá el botón de polígono (o rectángulo) de la izquierda para dibujar el lote. Doble clic o clic en el primer punto para cerrar.
            </p>
          )}
          {validation && (
            <div className="space-y-1">
              {showArea && validation.areaHa !== null && (
                <p>
                  <span className="font-medium">Área aproximada:</span> {validation.areaHa.toFixed(2)} ha
                </p>
              )}
              {showVertexCount && (
                <p>
                  <span className="font-medium">Vértices:</span> {validation.vertexCount.toLocaleString()} / {MAX_VERTICES.toLocaleString()}
                </p>
              )}
              {validation.errors.map((error, i) => (
                <p key={`e${i}`} className="text-red-600">✖ {error}</p>
              ))}
              {validation.warnings.map((warning, i) => (
                <p key={`w${i}`} className="text-amber-600">⚠ {warning}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
