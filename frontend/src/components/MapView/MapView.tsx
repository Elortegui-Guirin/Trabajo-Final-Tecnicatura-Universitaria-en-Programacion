// MapView.tsx - Mapa de solo lectura para mostrar un lote
// (envoltorio de MapEditor en modo readOnly)
import type { Feature } from "geojson"
import { MapEditor } from "./MapEditor"

export interface MapViewProps {
  lot: {
    id: string
    name: string
    area_ha: number
    geometry: Feature | null
    created_at: string
  }
  height?: string
}

export const MapView = ({ lot, height = "500px" }: MapViewProps) => (
  <MapEditor
    initialGeometry={lot.geometry}
    onGeometryChange={() => {}}
    readOnly
    height={height}
  />
)
