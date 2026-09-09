// RegisterForm.tsx - Formulario de registro
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { authApi } from "@/modules/auth/api/authApi"
import type { UserRegister } from "@/types/api"
import { useAuth } from "@/modules/auth/hooks/useAuth"

export const RegisterForm = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<UserRegister>({
    resolver: zodResolver(),
    defaultValues: { email: "", password: "", full_name: "" },
  })

  const onSubmit = async (data: UserRegister) => {
    setLoading(true)
    try {
      const userPublic = await authApi.register(data)
      // Después de registro, hacer login automático
      const meResult = await authApi.me()
      loginWithTokens(meResult, userPublic)
      navigate("/dashboard")
    } catch (error: any) {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">Registrarse</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Correo electrónico</label>
          <input
            {...register({ required: "Correo requerido", valid_email: "Email inválido" })} 
            type="email" 
            placeholder="ejemplo@email.com"
            className="w-full rounded border px-3 py-2"
          />
          {errors.email && <p className="text-red-500 text-sm">{errors.email}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Nombre completo</label>
          <input
            {...register({ required: "Nombre requerido" })} 
            type="text" 
            placeholder="Juan Pérez"
            className="w-full rounded border px-3 py-2"
          />
          {errors.full_name && <p className="text-red-500 text-sm">{errors.full_name}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Contraseña</label>
          <input
            {...register({ required: "Contraseña requerida", min_length: "Mínimo 8 caracteres" })} 
            type="password" 
            placeholder="••••••••••••••••"
            className="w-full rounded border px-3 py-2"
          />
          {errors.min_length && <p className="text-red-500 text-sm">{errors.min_length}</p>}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 rounded bg-green-600 text-white font-medium disabled:opacity-50"
        >
          {loading ? "Registrando..." : "Registrarse"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm">
        ¿Ya tienes cuenta? <a href="/login" className="underline text-blue-600">Inicia sesión</a>
      </p>
    </div>
  )
}