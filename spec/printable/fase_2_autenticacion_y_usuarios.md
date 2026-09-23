# Fase 2 – Autenticación y Usuarios

## 🎯 Objetivo de la Fase
Implementar autenticación completa basada en JWT: registro de usuarios, login con emisión de access/refresh tokens, middleware de protección de rutas, hash seguro de contraseñas, y gestión de sesión en frontend con persistencia.

## 📦 Artefactos Generados en esta Fase
- `backend/app/schemas/auth.py` – Pydantic: `UserRegister`, `UserLogin`, `TokenResponse`, `TokenRefresh`, `UserPublic`
- `backend/app/routers/auth.py` – Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
- `backend/app/services/auth_service.py` – Lógica: `register_user()`, `authenticate_user()`, `create_tokens()`, `get_current_user()`, `refresh_access_token()`
- `backend/app/core/security.py` – Implementación completa: `hash_password()`, `verify_password()`, `create_access_token()`, `create_refresh_token()`, `decode_token()`, `get_password_hash()`
- `backend/app/api/deps.py` – Dependencias: `get_current_user`, `get_current_active_user`, `require_auth`
- `backend/app/models/user.py` – Métodos de instancia: `verify_password()`, propiedades
- `backend/tests/test_auth.py` – Tests: registro, login, token refresh, acceso protegido, contraseña inválida
- `frontend/src/modules/auth/` – Módulo completo:
  - `components/RegisterForm.tsx` – Formulario registro (React Hook Form + Zod)
  - `components/LoginForm.tsx` – Formulario login
  - `components/ProtectedRoute.tsx` – Wrapper para rutas privadas
  - `hooks/useAuth.ts` – Hook para acceso a store + acciones
  - `store/authStore.ts` – Zustand: `user`, `accessToken`, `refreshToken`, `login()`, `logout()`, `refresh()`, `hydrate()`
  - `api/authApi.ts` – Llamadas API tipadas (TanStack Query mutations)
  - `pages/RegisterPage.tsx`, `LoginPage.tsx` – Páginas routables
- `frontend/src/components/Layout/PrivateLayout.tsx` – Layout con outlet protegido
- `frontend/src/pages/DashboardPage.tsx` – Página protegida de ejemplo (redirección post-login)

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Endpoints creados:**
| Método | Ruta | Body Request | Response | Descripción |
|--------|------|--------------|----------|-------------|
| POST | `/auth/register` | `UserRegister{email, password, full_name}` | `UserPublic{id, email, full_name, created_at}` | Crea usuario, hashea password, retorna datos públicos (201) |
| POST | `/auth/login` | `UserLogin{email, password}` | `TokenResponse{access_token, refresh_token, token_type}` | Valida credenciales, emite JWT access (15min) + refresh (7d) |
| POST | `/auth/refresh` | `TokenRefresh{refresh_token}` | `TokenResponse{access_token, refresh_token, token_type}` | Rotación de refresh token, nuevo par de tokens |
| GET | `/auth/me` | — (header Authorization: Bearer) | `UserPublic` | Usuario actual desde token válido |

**Modelos Pydantic/SQLModel:**
- `UserRegister`: email (EmailStr), password (min 8 chars), full_name (min 2)
- `UserLogin`: email, password
- `TokenResponse`: access_token, refresh_token, token_type="bearer"
- `TokenRefresh`: refresh_token
- `UserPublic`: id, email, full_name, created_at (sin hashed_password)

**Seguridad:**
- `passlib[bcrypt]` – `hash_password()` usa `bcrypt.hash()`, `verify_password()` usa `bcrypt.verify()`
- `python-jose` – JWT HS256, `access_token` exp 15min, `refresh_token` exp 7d, claims: `sub=user_id`, `type=access|refresh`, `iat`, `exp`
- Refresh token rotation: cada uso invalida el anterior y emite nuevo par
- Middleware `get_current_user` valida firma, expiración, tipo=access, usuario existe y activo

### Frontend (React + TypeScript)
**Componentes React construidos:**
- `RegisterForm` / `LoginForm`: `useForm` (RHF) + `zodResolver` (validación esquema), manejo errores API, loading states, redirección exitosa
- `ProtectedRoute`: verifica `authStore.isAuthenticated`, si no → redirect `/login?next=...`
- `PrivateLayout`: wrapper con header/nav + `<Outlet />` envuelto en `ProtectedRoute`

**Estado global (Zustand `authStore`):**
```typescript
interface AuthState {
  user: UserPublic | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (tokens: TokenResponse, user: UserPublic) => void;
  logout: () => void;
  refresh: () => Promise<void>; // llama POST /auth/refresh
  hydrate: () => void; // restaura desde localStorage al init
}
```
- Persistencia en `localStorage` (access+refresh tokens + user)
- Axios interceptor: adjunta `Authorization: Bearer <accessToken>`; en 401 → llama `refresh()` y reintenta 1 vez

**Queries/Mutations (TanStack Query):**
- `useRegisterMutation()`, `useLoginMutation()`, `useRefreshMutation()`
- `useCurrentUserQuery()` – GET /auth/me, enabled si `isAuthenticated`

### Base de Datos (PostgreSQL/PostGIS)
- **Migración 002** (`alembic/versions/002_add_user_security_fields.py` – opcional):
  - `ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;`
  - `ALTER TABLE users ADD COLUMN last_login TIMESTAMPTZ;`
  - Índice `idx_users_is_active` para queries de usuarios activos

## ✅ Criterios de Aceptación de la Fase
- [ ] `POST /auth/register` crea usuario, password hasheado en BD (no plaintext), retorna 201 + UserPublic
- [ ] `POST /auth/login` con credenciales válidas retorna access_token (JWT válido) + refresh_token
- [ ] `POST /auth/login` con password inválida retorna 401 "Credenciales inválidas"
- [ ] `GET /auth/me` con access_token válido retorna usuario; sin token o expirado → 401
- [ ] `POST /auth/refresh` rota refresh token: viejo invalidado, nuevo par emitido
- [ ] Frontend: registro → login automático → redirección a `/dashboard` funcional
- [ ] Frontend: refresh automático tras expiración access_token (interceptor) sin logout usuario
- [ ] Frontend: logout limpia store + localStorage + redirección a `/login`
- [ ] Tests backend: `pytest backend/tests/test_auth.py -v` → todos pasan
- [ ] `make lint` / `npm run lint` pasan

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (modelo User, DB, estructura backend/frontend, config JWT_SECRET)
- **Habilita**: Fase 3 (CRUD lotes requiere usuario autenticado + `user_id` en requests), Fase 4/5 (todas las rutas protegidas)