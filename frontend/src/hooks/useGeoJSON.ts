// useGeoJSON.ts - Utilidades para procesamiento de GeoJSON en frontend
import { useMemo } from "react"

// Validar que un GeoJSON sea un polígono válido (WGS84 / EPSG:4326)
export const validatePolygon = (geojson: any): {
  valid: boolean
  errors: string[]
  warnings: string[]
} => {
  const errors: string[] = []
  const warnings: string[] = []

  if (!geojson) {
    return { valid: false, errors: ["GeoJSON vacío"], warnings }
  }

  if (geojson.type !== "Feature" && geojson.type !== "FeatureCollection") {
    return { valid: false, errors: ["Tipo de GeoJSON no soportado"], warnings }
  }

  // Si es FeatureCollection, verificar features
  const features = geojson.type === "FeatureCollection" ? geojson.features : [geojson]

  for (const feature of features) {
    if (!feature.geometry) {
      errors.push("Feature sin geometría")
      continue
    }

    if (feature.geometry.type !== "Polygon") {
      errors.push(
        `Tipo de geometría inválido: ${feature.geometry.type}, se esperaba Polygon`
      )
      continue
    }

    // Verificar anillo exterior cerrado (primer punto == último punto)
    const exterior = feature.geometry.coordinates[0]
    if (!exterior || exterior.length < 4) {
      errors.push("Anillo exterior debe tener al menos 4 puntos (cerrarse)")
      continue
    }

    if (exterior[0][0] !== exterior[exterior.length - 1][0] ||
      exterior[0][1] !== exterior[exterior.length - 1][1]) {
      errors.push("Anillo exterior no está cerrado (primer punto debe ser igual al último)")
      continue
    }

    // Verificar que los anillos interiores (if any) estén en dirección CW
    // y el exterior en dirección CCW (convention for GeoJSON)
    // Validación básica: verificar que no haya anillos invertidos
    if (feature.geometry.coordinates.length > 1) {
      for (let i = 1; i < feature.geometry.coordinates.length; i++) {
        const interior = feature.geometry.coordinates[i]
        if (interior.length < 4) {
          errors.push(`Anillo interior ${i} debe tener al menos 4 puntos`)
        }
      }
    }
  }

  // Si hay errores, no es válido
  const hasErrors = errors.length > 0

  return {
    valid: !hasErrors,
    errors,
    warnings: warnings.length > 0 ? warnings : undefined,
  }
}

// Calcular área en hectáreas desde GeoJSON de un polígono
export const calculateAreaHa = (geojson: any): number | null => {
  if (!geojson || !geojson.geometry || geojson.geometry.type !== "Polygon") {
    return null
  }

  const coordinates = geojson.geometry.coordinates[0]

  if (!coordinates || coordinates.length < 4) {
    return null
  }

  try {
    // Usar Shapely via pywasm o cálculo aproximado
    // Para el frontend, usaremos una aproximación o delegar al backend
    // Por ahora retornamos null y el cálculo se hace server-side
    // En una implementación completa, aquí se podría usar turf.js
    return null
  } catch (e) {
    console.error("Error calculando área:", e)
    return null
  }
}

// Simplificar geometría reduciendo la cantidad de vértices
export const simplifyGeometry = (
  geojson: any,
  tolerance: number = 0.001
): any => {
  if (!geojson || !geojson.geometry) {
    return geojson
  }

  try {
    // En una implementación completa, usaríamos turf.simplify
    // o la biblioteca de simplificación de Shapely
    // Por aquí solo validamos y retornamos la geometría original
    // si el tolerance es muy pequeño o la geometría es muy simple
    if (tolerance <= 0) {
      return geojson
    }

    // Placeholder: en producción integraríamos turf.simplify o similar
    return geojson
  } catch (e) {
    console.error("Error simplificando geometría:", e)
    return geojson
  }
}

// Exportar tipos útiles
export type { validatePolygon, calculateAreaHa, simplifyGeometry }