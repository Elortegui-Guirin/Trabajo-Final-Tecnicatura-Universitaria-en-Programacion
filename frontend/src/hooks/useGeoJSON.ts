// useGeoJSON.ts - Utilidades para validar y medir polígonos GeoJSON en el frontend
// (validación rápida para feedback inmediato; la validación definitiva la hace el backend)

export const MAX_VERTICES = 5000
export const MIN_AREA_HA = 0.01
export const MAX_AREA_HA = 10000

type Position = number[]

/** Devuelve el anillo exterior de un Feature/Geometry Polygon (o null). */
const getExteriorRing = (geojson: any): Position[] | null => {
  const geometry = geojson?.type === "Feature" ? geojson.geometry : geojson
  if (!geometry || geometry.type !== "Polygon") return null
  const ring = geometry.coordinates?.[0]
  return Array.isArray(ring) ? ring : null
}

/** Cantidad de vértices del anillo exterior (sin contar el punto de cierre). */
export const getVertexCount = (geojson: any): number => {
  const ring = getExteriorRing(geojson)
  if (!ring || ring.length === 0) return 0
  const first = ring[0]
  const last = ring[ring.length - 1]
  const closed = first && last && first[0] === last[0] && first[1] === last[1]
  return closed ? ring.length - 1 : ring.length
}

/**
 * Área aproximada en hectáreas (fórmula de área esférica, suficiente para feedback).
 * El área definitiva se calcula en el backend proyectando a UTM.
 */
export const calculateAreaHa = (geojson: any): number | null => {
  const ring = getExteriorRing(geojson)
  if (!ring || ring.length < 4) return null
  const R = 6371008.8 // radio medio terrestre (m)
  const toRad = (d: number) => (d * Math.PI) / 180
  let total = 0
  for (let i = 0; i < ring.length - 1; i++) {
    const [lon1, lat1] = ring[i]
    const [lon2, lat2] = ring[i + 1]
    total += toRad(lon2 - lon1) * (2 + Math.sin(toRad(lat1)) + Math.sin(toRad(lat2)))
  }
  const areaM2 = Math.abs((total * R * R) / 2)
  return areaM2 / 10000
}

/** Valida un polígono (Feature o Geometry) y devuelve errores, advertencias, vértices y área. */
export const validatePolygon = (geojson: any): {
  valid: boolean
  errors: string[]
  warnings: string[]
  vertexCount: number
  areaHa: number | null
} => {
  const errors: string[] = []
  const warnings: string[] = []

  const ring = getExteriorRing(geojson)
  if (!ring) {
    return { valid: false, errors: ["La geometría debe ser un polígono"], warnings, vertexCount: 0, areaHa: null }
  }

  const vertexCount = getVertexCount(geojson)
  const areaHa = calculateAreaHa(geojson)

  if (ring.length < 4) errors.push("El polígono necesita al menos 3 vértices")
  if (vertexCount > MAX_VERTICES) errors.push(`Demasiados vértices (${vertexCount}). Máximo: ${MAX_VERTICES}`)
  else if (vertexCount > MAX_VERTICES * 0.8) warnings.push("La geometría está cerca del límite de vértices")

  const outOfRange = ring.some(([lon, lat]) => lon < -180 || lon > 180 || lat < -90 || lat > 90)
  if (outOfRange) errors.push("Coordenadas fuera de rango (deben ser lon/lat WGS84)")

  if (areaHa !== null) {
    if (areaHa < MIN_AREA_HA) errors.push(`Área demasiado pequeña (${areaHa.toFixed(4)} ha). Mínimo: ${MIN_AREA_HA} ha`)
    if (areaHa > MAX_AREA_HA) errors.push(`Área demasiado grande (${areaHa.toFixed(0)} ha). Máximo: ${MAX_AREA_HA} ha`)
    if (areaHa < 11 && areaHa >= MIN_AREA_HA) {
      warnings.push("El lote es más chico que un píxel de los mapas (~11 ha): el resultado será aproximado")
    }
  }

  return { valid: errors.length === 0, errors, warnings, vertexCount, areaHa }
}

/**
 * Si el polígono supera MAX_VERTICES, conserva 1 de cada N vértices del anillo exterior.
 * Devuelve el mismo objeto si no hace falta simplificar.
 */
export const simplifyGeometry = (geojson: any, maxVertices: number = MAX_VERTICES): any => {
  const ring = getExteriorRing(geojson)
  if (!ring || ring.length - 1 <= maxVertices) return geojson

  const factor = Math.ceil((ring.length - 1) / maxVertices)
  const simplified = ring.filter((_, index) => index % factor === 0)
  const first = simplified[0]
  const last = simplified[simplified.length - 1]
  if (first[0] !== last[0] || first[1] !== last[1]) simplified.push(first)

  const copy = JSON.parse(JSON.stringify(geojson))
  if (copy.type === "Feature") copy.geometry.coordinates[0] = simplified
  else copy.coordinates[0] = simplified
  return copy
}
