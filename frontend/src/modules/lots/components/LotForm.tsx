// LotForm.tsx - Formulario crear/editar lote con mapa
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useNavigate, useParams } from "react-router-dom"
import { MapEditor } from "@/components/MapView/MapEditor"
import { useCreateLot, useUpdateLot } from "@/modules/lots/hooks/useLots"
import type { LotCreate, LotUpdate, LotRead, GeoJSONPolygon } from "@/types/api"

const lotSchema = z.object({
  name: z.string().min(1, "Nombre requerido").max(255),
  geometry: z.object({
    type: z.literal("Polygon"),
    coordinates: z.array(
      z.array(z.array(z.number()))
    ), // [[[lon, lat], ...], [[lon, lat], ...]] para interiores
  }),
  change_reason: z.string().max(500).optional(),
})

type LotFormData = z.infer<typeof lotSchema>

export function LotForm() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id

  const createMutation = useCreateLot()
  const updateMutation = useUpdateLot()

  const [geometry, setGeometry] = useState<GeoJSONPolygon | null>(null)
  const [areaHa, setAreaHa] = useState<number | null>(null)
  const [editing, setEditing] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<LotFormData>({
    resolver: zodResolver(lotSchema),
    defaultValues: { name: "", geometry: { type: "Polygon", coordinates: [[]] }, change_reason: "" },
  })

  // Si es edición, cargar datos (en implementación real usaríamos useLot hook)
  useEffect(() => {
    if (isEdit && id) {
      // Cargar lote existente
    }
  }, [isEdit, id])

  const handleGeometryChange = (geojson: any) => {
    if (geojson?.geometry?.type === "Polygon" && geojson.geometry.coordinates?.[0]?.length >= 4) {
      const normalized: GeoJSONPolygon = {
        type: "Polygon",
        coordinates: geojson.geometry.coordinates,
      }
      setGeometry(normalized)
      setValue("geometry", normalized, { shouldValidate: true })
    } else {
      setGeometry(null)
      setValue("geometry", { type: "Polygon", coordinates: [[]] }, { shouldValidate: true })
    }
  }

  const onSubmit = async (data: LotFormData) => {
    try {
      if (isEdit && id) {
        await updateMutation.mutateAsync({ 
          id, 
          data: { 
            name: data.name, 
            geometry: data.geometry, 
            change_reason: data.change_reason 
          } 
        })
      } else {
        await createMutation.mutateAsync(data)
      }
      navigate("/lots")
    } catch (err: any) {
      // Errores de validación server-side
      if (err?.response?.data?.detail) {
        // Manejar errores de geometría/área inválida
      }
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Nombre */}
      <div>
        <label htmlFor="name" className="label">Nombre del lote</label>
        <input
          {...register("name")}
          id="name"
          type="text"
          className={`input ${errors.name ? "border-red-300 focus:ring-red-500" : ""}`}
          placeholder="Ej: Lote Norte, Potrero 1, Campo Principal"
        />
        {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
      </div>

      {/* Motivo del cambio (solo edición) */}
      {isEdit && (
        <div>
          <label htmlFor="change_reason" className="label">Motivo del cambio (opcional)</label>
          <textarea
            {...register("change_reason")}
            id="change_reason"
            rows={3}
            className="input"
            placeholder="Ej: Corrección de límites, ampliación de área, rotación de cultivos..."
          />
          {errors.change_reason && <p className="mt-1 text-sm text-red-600">{errors.change_reason.message}</p>}
        </div>
      )}

      {/* Mapa */}
      <div>
        <label className="label">Geometría del lote</label>
        <div className="relative">
          <MapEditor
            initialGeometry={geometry ? { type: "Feature", properties: {}, geometry } : null}
            onGeometryChange={handleGeometryChange}
            readOnly={editing}
            height="500px"
          />
          {errors.geometry && (
            <div className="absolute bottom-4 left-4 right-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
              {errors.geometry.message}
            </div>
          )}
        </div>
      </div>

      {/* Área calculada */}
      {areaHa !== null && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Área calculada (aprox):</span>
            <span className="text-2xl font-bold text-primary-600">{areaHa.toFixed(2)} ha</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Valor definitivo calculado por el servidor al guardar (mín. 0.01 ha)</p>
        </div>
      )}

      {/* Botones */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={() => navigate("/lots")}
          className="btn-secondary"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={createMutation.isPending || updateMutation.isPending}
          className="btn-primary"
        >
          {isEdit ? "Actualizar" : "Crear lote"}
          {(createMutation.isPending || updateMutation.isPending) && "..."}
        </button>
      </div>
    </form>
  )
}