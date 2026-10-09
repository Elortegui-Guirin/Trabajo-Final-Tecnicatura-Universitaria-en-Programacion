// useGeoJSON.ts - Utilidades para procesamiento de GeoJSON en frontend
import { useMemo } from "react"

// Constantes de validación (deben coincidir con backend)
export const MAX_VERTICES = 5000
export const MIN_AREA_HA = 0.01  // 100 m²
export const MAX_AREA_HA = 10000  // 10,000 ha
export const SIMPLIFY_TOLERANCE = 0.00001  // ~1m en WGS84

// Interfaces
export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  vertexCount: number
  areaHa: number | null
}

// Validar que un GeoJSON sea un polígono válido (WGS84 / EPSG:4326)
export const validatePolygon = (geojson: any): ValidationResult => {
  const errors: string[] = []
  const warnings: string[] = []
  let vertexCount = 0
  let areaHa: number | null = null

  if (!geojson) {
    return { valid: false, errors: ["GeoJSON vacío"], warnings, vertexCount: 0, areaHa: null }
  }

  // Normalizar: si es FeatureCollection, tomar la primera feature
  let feature = geojson
  if (geojson.type === "FeatureCollection") {
    if (!geojson.features || geojson.features.length === 0) {
      return { valid: false, errors: ["FeatureCollection vacía"], warnings, vertexCount: 0, areaHa: null }
    }
    feature = geojson.features[0]
    warnings.push("FeatureCollection recibida: se tomará la primera feature")
  }

  if (feature.type === "Feature") {
    feature = feature.geometry
  }

  if (!feature) {
    return { valid: false, errors: ["Geometría vacía"], warnings, vertexCount: 0, areaHa: null }
  }

  if (feature.type !== "Polygon") {
    return { 
      valid: false, 
      errors: [`Tipo de geometría inválido: ${feature.type}, se esperaba Polygon`], 
      warnings, 
      vertexCount: 0, 
      areaHa: null 
    }
  }

  const coordinates = feature.coordinates
  if (!coordinates || coordinates.length < 1) {
    return { valid: false, errors: ["Polygon sin coordenadas"], warnings, vertexCount: 0, areaHa: null }
  }

  const exterior = coordinates[0]
  if (!exterior || exterior.length < 4) {
    return { valid: false, errors: ["Anillo exterior debe tener al menos 4 puntos (cerrarse)"], warnings, vertexCount: 0, areaHa: null }
  }

  // Verificar anillo exterior cerrado (primer punto == último punto)
  const first = exterior[0]
  const last = exterior[exterior.length - 1]
  if (first[0] !== last[0] || first[1] !== last[1]) {
    errors.push("Anillo exterior no está cerrado (primer punto debe ser igual al último)")
  }

  // Contar vértices (excluyendo el punto de cierre)
  vertexCount = exterior.length - 1

  // Verificar vértices máximos
  if (vertexCount > 5000) {
    warnings.push(`Geometría compleja: ${vertexCount} vértices (máx. 5000). Se simplificará automáticamente al enviar.`)
  } else if (vertexCount > 4000) {
    warnings.push(`Geometría compleja: ${vertexCount} vértices (máx. 5000)`)
  }

  // Verificar anillos interiores
  if (coordinates.length > 1) {
    for (let i = 1; i < coordinates.length; i++) {
      const interior = coordinates[i]
      if (interior.length < 4) {
        errors.push(`Anillo interior ${i} debe tener al menos 4 puntos`)
      }
    }
  }

  // Calcular área aproximada (shoelace formula en grados², luego conversión aproximada)
  try {
    let areaDeg2 = 0
    const coords = exterior
    for (let i = 0; i < coords.length - 1; i++) {
      areaDeg2 += coords[i][0] * coords[i + 1][1] - coords[i + 1][0] * coords[i][1]
    }
    areaDeg2 = Math.abs(areaDeg2) / 2
    // Aproximación rough: 1 grado² ≈ 12300 km² en latitud media
    // Para feedback visual only, server valida definitivo
    areaHa = areaDeg2 * 12300 * 100
  } catch (e) {
    console.warn("Error calculando área aproximada:", e)
  }

  const hasErrors = errors.length > 0

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    vertexCount,
    areaHa,
  }
}

// Calcular área en hectáreas desde GeoJSON de un polígono
export const calculateAreaHa = (geojson: any): number | null => {
  if (!geojson) return null
  
  let feature = geojson
  if (geojson.type === "FeatureCollection") {
    if (!geojson.features || geojson.features.length === 0) return null
    feature = geojson.features[0]
  }
  if (feature.type === "Feature") {
    feature = feature.geometry
  }
  
  if (!feature || feature.type !== "Polygon") return null
  
  const coordinates = feature.coordinates[0]
  if (!coordinates || coordinates.length < 4) return null
  
  try {
    let areaDeg2 = 0
    for (let i = 0; i < coordinates.length - 1; i++) {
      areaDeg2 += coordinates[i][0] * coordinates[i + 1][1] - coordinates[i + 1][0] * coordinates[i][1]
    }
    areaDeg2 = Math.abs(areaDeg2) / 2
    // Aproximación rough: 1 grado² ≈ 12300 km² en latitud media
    return Math.round(areaDeg2 * 12300 * 100 * 100) / 100  // redondear a 2 decimales
  } catch (e) {
    console.error("Error calculando área:", e)
    return null
  }
}

// Simplificar geometría usando Douglas-Peucker (Ramer-Douglas-Peucker)
// Implementación básica - en producción usar turf.simplify
export const simplifyGeometry = (
  geojson: any,
  tolerance: number = 0.00001
): any => {
  if (!geojson || !geojson.geometry) {
    return geojson
  }

  if (tolerance <= 0) {
    return geojson
  }

  try {
    // Extraer geometría
    let feature = geojson
    if (geojson.type === "FeatureCollection") {
      feature = geojson.features[0]
    }
    if (feature.type === "Feature") {
      feature = feature.geometry
    }
    
    if (!feature || feature.type !== "Polygon") {
      return geojson
    }

    const coordinates = feature.coordinates
    const exterior = coordinates[0]
    
    // Douglas-Peucker simplificación
    const simplifiedExterior = douglasPeucker(exterior, tolerance)
    
    // Asegurar que el anillo esté cerrado
    if (simplifiedExterior.length < 4) {
      return geojson
    }
    
    // Cerrar anillo si no lo está
    if (simplifiedExterior[0][0] !== simplifiedExterior[simplifiedExterior.length - 1][0] ||
        simplifiedExterior[0][1] !== simplifiedExterior[simplifiedExterior.length - 1][1]) {
      simplifiedExterior.push([...simplifiedExterior[0]])
    }

    // Reconstruir geometría
    const newFeature = {
      ...feature,
      coordinates: [simplifiedExterior, ...feature.coordinates.slice(1)]
    }

    // Reconstruir GeoJSON original
    let result = geojson
    if (geojson.type === "FeatureCollection") {
      result = {
        ...geojson,
        features: [{ ...geojson.features[0], geometry: newFeature }]
      }
    } else if (geojson.type === "Feature") {
      result = { ...geojson, geometry: newFeature }
    } else {
      result = { ...geojson, coordinates: [simplifiedExterior, ...feature.coordinates.slice(1)] }
    }

    return result
  } catch (e) {
    console.error("Error simplificando geometría:", e)
    return geojson
  }
}

// Algoritmo Douglas-Peucker (Ramer-Douglas-Peucker)
function douglasPeucker(points: number[][], tolerance: number): number[][] {
  if (points.length < 3) return points

  // Encontrar el punto con la máxima distancia
  let maxDist = 0
  let index = 0
  const end = points.length - 1

  for (let i = 1; i < end; i++) {
    const dist = perpendicularDistance(points[i], points[0], points[end])
    if (dist > maxDist) {
      maxDist = dist
      index = i
    }
  }

  // Si la distancia máxima es mayor que la tolerancia, dividir recursivamente
  if (maxDist > tolerance) {
    const left = douglasPeucker(points.slice(0, index + 1), tolerance)
    const right = douglasPeucker(points.slice(index), tolerance)
    // Combinar (eliminando el punto duplicado en el medio)
    return left.slice(0, -1).concat(right)
  } else {
    return [points[0], points[end]]
  }
}

// Calcular distancia perpendicular de un punto a un segmento
function perpendicularDistance(point: number[], lineStart: number[], lineEnd: number[]): number {
  const x = point[0]
  const y = point[1]
  const x1 = lineStart[0]
  const y1 = lineStart[1]
  const x2 = lineEnd[0]
  const y2 = lineEnd[1]

  const A = x - x1
  const B = y - y1
  const C = x2 - x1
  const D = y2 - y1

  const dot = A * C + B * D
  const lenSq = C * C + D * D
  let param = -1
  
  if (lenSq !== 0) {
    param = dot / lenSq
  }

  let xx, yy
  if (param < 0) {
    xx = x1
    yy = y1
  } else if (param > 1) {
    xx = x2
    yy = y2
  } else {
    xx = x1 + param * C
    yy = y1 + param * D
  }

  const dx = x - xx
  const dy = y - yy
  return Math.sqrt(dx * dx + dy * dy)
}

// Calcular área en hectáreas desde GeoJSON
export const calculateAreaHa = (geojson: any): number | null => {
  if (!geojson) return null
  
  let feature = geojson
  if (geojson.type === "FeatureCollection") {
    if (!geojson.features || geojson.features.length === 0) return null
    feature = geojson.features[0]
  }
  if (feature.type === "Feature") {
    feature = feature.geometry
  }
  
  if (!feature || feature.type !== "Polygon") return null
  
  const coordinates = feature.coordinates[0]
  if (!coordinates || coordinates.length < 4) return null
  
  try {
    let areaDeg2 = 0
    for (let i = 0; i < coordinates.length - 1; i++) {
      areaDeg2 += coordinates[i][0] * coordinates[i + 1][1] - coordinates[i + 1][0] * coordinates[i][1]
    }
    areaDeg2 = Math.abs(areaDeg2) / 2
    // Aproximación rough: 1 grado² ≈ 12300 km² en latitud media
    return Math.round((areaDeg2 * 12300 * 100) * 100) / 100  // redondear a 2 decimales
  } catch (e) {
    console.error("Error calculando área:", e)
    return null
  }
}

// Obtener conteo de vértices
export const getVertexCount = (geojson: any): number => {
  if (!geojson) return 0
  
  let feature = geojson
  if (geojson.type === "FeatureCollection") {
    feature = geojson.features[0]
  }
  if (feature.type === "Feature") {
    feature = feature.geometry
  }
  
  if (!feature || feature.type !== "Polygon") return 0
  if (!feature.coordinates || !feature.coordinates[0]) return 0
  
  return feature.coordinates[0].length - 1
}

// Exportar tipos útiles
export type { ValidationResult }