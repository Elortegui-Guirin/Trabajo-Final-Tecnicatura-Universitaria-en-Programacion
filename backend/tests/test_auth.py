# Tests de autenticación - pytest-asyncio
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Prueba el registro de un nuevo usuario."""
    response = await async_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_login_valid(async_client: AsyncClient):
    """Prueba login con credenciales válidas."""
    # Primero registramos
    await async_client.post(
        "/auth/register",
        json={"email": "test2@example.com", "password": "password123", "full_name": "Test User 2"},
    )
    # Luego login
    response = await async_client.post(
        "/auth/login",
        json={"email": "test2@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    """Prueba login con password inválido."""
    await async_client.post(
        "/auth/register",
        json={"email": "test3@example.com", "password": "password123", "full_name": "Test User 3"},
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "test3@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_token_refresh(async_client: AsyncClient):
    """Prueba el refresh de token."""
    # Registrar y login
    await async_client.post(
        "/auth/register",
        json={"email": "test4@example.com", "password": "password123", "full_name": "Test User 4"},
    )
    login_response = await async_client.post(
        "/auth/login",
        json={"email": "test4@example.com", "password": "password123"},
    )
    tokens = login_response.json()
    
    # Usar refresh token
    response = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # El refresh token viejo debería haber sido invalidado
    # Intentar usar el mismo refresh token debería fallar
    response2 = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response2.status_code == 401  # Should be invalidated


@pytest.mark.asyncio
async def test_get_me_with_token(async_client: AsyncClient):
    """Prueba GET /auth/me con token válido."""
    # Registrar y login
    await async_client.post(
        "/auth/register",
        json={"email": "test5@example.com", "password": "password123", "full_name": "Test User 5"},
    )
    login_response = await async_client.post(
        "/auth/login",
        json={"email": "test5@example.com", "password": "password123"},
    )
    tokens = login_response.json()
    
    # Acceder con access_token
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test5@example.com"