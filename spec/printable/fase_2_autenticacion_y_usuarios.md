# Fase 2 – Autenticación y Usuarios

## 🎯 Objetivo de la Fase
Implementar autenticación completa basada en JWT: registro de usuarios, login con emisión de access/refresh tokens, middleware de protección de rutas, hash seguro de contraseñas, y gestión de sesión en frontend con persistencia. **Incluye mejoras: verificación de email, recuperación de contraseña, control de intentos de login.**

## 📦 Artefactos Generados en esta Fase
- `backend/app/schemas/auth.py` – Pydantic: `UserRegister`, `UserLogin`, `TokenResponse`, `TokenRefresh`, `UserPublic`, **`VerifyEmailRequest`, `ResendVerificationRequest`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `AuthMessageResponse`**
- `backend/app/routers/auth.py` – Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`, **`POST /auth/verify-email`, `POST /auth/resend-verification`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/logout`**
- `backend/app/services/auth_service.py` – Lógica: `register_user()`, `authenticate_user()`, `create_tokens()`, `get_current_user()`, `refresh_access_token()`, **`verify_email()`, `resend_verification()`, `forgot_password()`, `reset_password()`**
- `backend/app/core/security.py` – Implementación completa: `hash_password()`, `verify_password()`, `create_access_token()`, `create_refresh_token()`, `decode_token()`, **`create_verification_token()`, `create_reset_token()`, `generate_secure_token()`**
- `backend/app/api/deps.py` – Dependencias: `get_current_user`, `get_current_active_user`, `require_auth` (con verificación de cuenta bloqueada y soft-delete)
- `backend/app/models/user.py` – Métodos: `verify_password()`, **`is_locked()`, `record_failed_login()`, `reset_failed_logins()`**, campos: `email_verified`, `verification_token`, `reset_token`, `failed_login_attempts`, `locked_until`
- `backend/tests/test_auth.py` – Tests: registro, login, token refresh, acceso protegido, contraseña inválida, **verificación email, reset password, rate limiting, account lockout**
- `backend/alembic/versions/004_auth_improvements.py` – Migración: campos verificación, reset, intentos fallidos, bloqueo
- `frontend/src/modules/auth/` – Módulo completo:
  - `components/RegisterForm.tsx` – Formulario registro (React Hook Form + Zod)
  - `components/LoginForm.tsx` – Formulario login
  - `components/ProtectedRoute.tsx` – Wrapper para rutas privadas
  - `hooks/useAuth.ts` – Hook para acceso a store + acciones
  - `store/authStore.ts` – Zustand: `user`, `accessToken`, `refreshToken`, `login()`, `logout()`, `refresh()`, `hydrate()`
  - `api/authApi.ts` – Llamadas API tipadas: **`verifyEmail()`, `resendVerification()`, `forgotPassword()`, `resetPassword()`, `logout()`**
  - `pages/RegisterPage.tsx`, `LoginPage.tsx` – Páginas routables
  - **Nuevas páginas: `VerifyEmailPage.tsx`, `ForgotPasswordPage.tsx`, `ResetPasswordPage.tsx`**
- `frontend/src/components/Layout/PrivateLayout.tsx` – Layout con outlet protegido
- `frontend/src/pages/DashboardPage.tsx` – Página protegida de ejemplo

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Endpoints creados:**
| Método | Ruta | Body Request | Response | Descripción |
|--------|------|--------------|----------|-------------|
| POST | `/auth/register` | `UserRegister{email, password, full_name}` | `UserPublic{id, email, full_name, created_at, email_verified}` | Crea usuario, hashea password, genera token verificación, envía email (201) |
| POST | `/auth/login` | `UserLogin{email, password}` | `TokenResponse{access_token, refresh_token, token_type}` | Valida credenciales, control intentos, bloqueo 15min tras 5 fallos, emite JWT access (15min) + refresh (7d) |
| POST | `/auth/refresh` | `TokenRefresh{refresh_token}` | `TokenResponse{access_token, refresh_token, token_type}` | Rotación de refresh token, nuevo par de tokens |
| GET | `/auth/me` | — (header Authorization: Bearer) | `UserPublic` | Usuario actual desde token válido |
| POST | `/auth/verify-email` | `VerifyEmailRequest{token}` | `AuthMessageResponse` | Verifica email con token (JWT o seguro) |
| POST | `/auth/resend-verification` | `ResendVerificationRequest{email}` | `AuthMessageResponse` | Reenvía email verificación (idempotente) |
| POST | `/auth/forgot-password` | `ForgotPasswordRequest{email}` | `AuthMessageResponse` | Envía token reset password (expira 1h) |
| POST | `/auth/reset-password` | `ResetPasswordRequest{token, new_password, confirm_password}` | `AuthMessageResponse` | Restablece contraseña con token válido |
| POST | `/auth/logout` | — | `AuthMessageResponse` | Logout server-side (logging/auditoría) |

**Modelos Pydantic/SQLModel (nuevos):**
- `VerifyEmailRequest`: token (str)
- `ResendVerificationRequest`: email (EmailStr)
- `ForgotPasswordRequest`: email (EmailStr)
- `ResetPasswordRequest`: token, new_password (min 8), confirm_password
- `AuthMessageResponse`: message (str)

**Seguridad mejorada:**
- `passlib[bcrypt]` – `hash_password()` usa `bcrypt.hash()`, `verify_password()` usa `bcrypt.verify()`
- `python-jose` – JWT HS256, `access_token` exp 15min, `refresh_token` exp 7d, claims: `sub=user_id`, `type=access|refresh|verification|reset`, `iat`, `exp`
- Refresh token rotation: cada uso invalida el anterior y emite nuevo par
- **Rate limiting por IP**: 10 req/15min en `/auth/login`
- **Account lockout**: 5 intentos fallidos → bloqueo 15 min
- **Email verification**: Token seguro (no JWT) expira 24h, enviado por email
- **Password reset**: Token seguro expira 1h, invalidado tras uso
- **Seguridad tokens**: Tokens de verificación/reset son `secrets.token_urlsafe(32)` (no JWT)
- Middleware `get_current_user` valida firma, expiración, tipo=access, usuario existe, activo, no soft-deleted, **no bloqueado**

### Frontend (React + TypeScript)
**Nuevos componentes/páginas:**
- `VerifyEmailPage.tsx` – Página verificación email (lee token de query params)
- `ForgotPasswordPage.tsx` – Formulario solicitud reset password
- `ResetPasswordPage.tsx` – Formulario nueva contraseña (token en query params)
- `api/authApi.ts` – Nuevos métodos: `verifyEmail()`, `resendVerification()`, `forgotPassword()`, `resetPassword()`, `logout()`

**Estado global (Zustand `authStore`):** Sin cambios estructurales, compatible con nuevos flujos.

### Base de Datos (PostgreSQL/PostGIS)
- **Migración 004** (`alembic/versions/004_auth_improvements.py`):
  - `email_verified` (boolean, default false)
  - `verification_token`, `verification_token_expires` + índice
  - `reset_token`, `reset_token_expires` + índice
  - `failed_login_attempts` (int, default 0)
  - `locked_until` (timestamp, nullable) + índice

## ✅ Criterios de Aceptación de la Fase
- [ ] `POST /auth/register` crea usuario, password hasheado, genera token verificación, envía email (log), retorna 201 + UserPublic con `email_verified: false`
- [ ] `POST /auth/login` con credenciales válidas retorna access_token + refresh_token
- [ ] `POST /auth/login` con password inválida incrementa contador, 5 fallos → 423 Locked (15 min)
- [ ] `POST /auth/login` rate limited: 10 req/15min por IP → 429 Too Many Requests
- [ ] `GET /auth/me` con access_token válido retorna usuario + `email_verified`; sin token/expirado → 401
- [ ] `POST /auth/refresh` rota refresh token: viejo invalidado, nuevo par emitido
- [ ] `POST /auth/verify-email` con token válido → `email_verified=true`, token consumido
- [ ] `POST /auth/resend-verification` reenvía email (idempotente, no revela si email existe)
- [ ] `POST /auth/forgot-password` envía token reset (expira 1h), no revela si email existe
- [ ] `POST /auth/reset-password` con token válido actualiza password, invalida token, resetea contadores fallos
- [ ] Frontend: registro → email verificación → login → dashboard funcional
- [ ] Frontend: forgot password → email → reset password → login funcional
- [ ] Frontend: rate limiting y account lockout mostrados en UI
- [ ] Tests backend: `pytest backend/tests/test_auth.py -v` → todos pasan (incl. nuevos casos)
- [ ] `make lint` / `npm run lint` pasan

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (modelo User, DB, estructura backend/frontend, config JWT_SECRET)
- **Habilita**: Fase 3 (CRUD lotes requiere usuario autenticado + `user_id` en requests), Fase 4/5 (todas las rutas protegidas)