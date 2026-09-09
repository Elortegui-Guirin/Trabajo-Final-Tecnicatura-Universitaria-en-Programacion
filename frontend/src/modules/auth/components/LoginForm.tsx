// LoginForm.tsx - Formulario de login
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { authApi } from "@/modules/auth/api/authApi"
import type { UserLogin } from "@/types/api"
import { useAuth } from "@/modules/auth/hooks/useAuth"

export const LoginForm = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const { login, isAuthenticated } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<UserLogin>({
    resolver: zodResolver(),
    defaultValues: { email: "", password: "" },
  })

  const onSubmit = async (data: UserLogin) => {
    setLoading(true)
    try {
      const result = await authApi.login(data)
      loginWithTokens(result, null) // user se obtiene de /auth/me después
      navigate("/dashboard")
    } catch (error: any) {
      // Error de credenciales inválidas se muestra automáticamente
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">Iniciar sesión</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Correo electrónico</label>
          <input
            {...register({ required: "Correo requerido" })} 
            type="email" 
            placeholder="ejemplo@email.com"
            className="w-full rounded border px-3 py-2"
          />
          {errors.email && <p className="text-red-500 text-sm">{errors.email}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Contraseña</label>
          <input
            {...register({ required: "Contraseña requerida" })} 
            type="password" 
            placeholder="••••••••"
            className="w-full rounded border px-3 py-2"
          />
          {errors.password && <p className="text-red-500 text-sm">{errors.password}</p>}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 rounded bg-blue-600 text-white font-medium disabled:opacity-50"
        >
          {loading ? "Iniciando sesión..." : "Ingresar"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm">
        ¿No tienes cuenta? <a href="/register" className="underline text-blue-600">Regístrate</a>
      </p>
    </div>
  )
}