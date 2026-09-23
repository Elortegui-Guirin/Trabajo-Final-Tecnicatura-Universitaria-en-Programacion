# Tests de lotes - pytest-asyncio
import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.main import app
from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
async def test_user(async_client: AsyncClient):
    """Crea un usuario de prueba y retorna sus credenciales + token."""
    # Registrar
    reg_response = await async_client.post(
        "/auth/register",
        json={"email": "lottest@example.com", "password": "password123", "full_name": "Lot Test User"},
    )
    assert reg_response.status_code == 201
    
    # Login
    login_response = await async_client.post(
        "/auth/login",
        json={"email": "lottest@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    return {"tokens": tokens, "email": "lottest@example.com"}


@pytest.fixture
def auth_headers(test_user):
    """Headers con access token."""
    return {"Authorization": f"Bearer {test_user['tokens']['access_token']}"}


@pytest.fixture
def sample_polygon():
    """Polígono GeoJSON válido (cuadrado aprox 100ha en Argentina)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [-58.5, -34.5],
            [-58.5, -34.4],
            [-58.4, -34.4],
            [-58.4, -34.5],
            [-58.5, -34.5]
        ]]
    }


@pytest.mark.asyncio
async def test_create_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba creación de lote con geometría válida."""
    response = await async_client.post(
        "/lots",
        json={"name": "Lote Norte", "geometry": sample_polygon},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Lote Norte"
    assert "id" in data
    assert data["area_ha"] > 0
    assert data["geometry"]["type"] == "Polygon"


@pytest.mark.asyncio
async def test_create_lot_invalid_geometry(async_client: AsyncClient, auth_headers):
    """Prueba creación con geometría inválida (no polígono)."""
    invalid_geom = {
        "type": "Point",
        "coordinates": [-58.5, -34.5]
    }
    response = await async_client.post(
        "/lots",
        json={"name": "Lote Inválido", "geometry": invalid_geom},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_lots(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba listado paginado de lotes."""
    # Crear 2 lotes
    for i in range(2):
        await async_client.post(
            "/lots",
            json={"name": f"Lote {i}", "geometry": sample_polygon},
            headers=auth_headers,
        )
    
    response = await async_client.get("/lots?page=1&size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert data["page"] == 1
    assert data["size"] == 10


@pytest.mark.asyncio
async def test_get_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba obtención de lote por ID."""
    # Crear lote
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Detalle", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    # Obtener
    response = await async_client.get(f"/lots/{lot_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lot_id
    assert data["name"] == "Lote Detalle"


@pytest.mark.asyncio
async def test_update_lot_name(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba actualización de nombre."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Nombre Original", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    response = await async_client.patch(
        f"/lots/{lot_id}",
        json={"name": "Nombre Actualizado"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Nombre Actualizado"


@pytest.mark.asyncio
async def test_update_lot_geometry(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba actualización de geometría (recalcula área)."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Geo Update", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    original_area = create_resp.json()["area_ha"]
    
    # Nuevo polígono más grande
    bigger_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [-58.6, -34.6],
            [-58.6, -34.3],
            [-58.3, -34.3],
            [-58.3, -34.6],
            [-58.6, -34.6]
        ]]
    }
    
    response = await async_client.patch(
        f"/lots/{lot_id}",
        json={"geometry": bigger_polygon},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["area_ha"] > original_area


@pytest.mark.asyncio
async def test_delete_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba eliminación de lote."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote A Borrar", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    response = await async_client.delete(f"/lots/{lot_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verificar que ya no existe
    get_resp = await async_client.get(f"/lots/{lot_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_lot_ownership_isolation(async_client: AsyncClient, sample_polygon):
    """Prueba que usuarios solo ven sus propios lotes."""
    # Usuario 1
    await async_client.post("/auth/register", json={"email": "user1@test.com", "password": "pass123", "full_name": "User 1"})
    login1 = await async_client.post("/auth/login", json={"email": "user1@test.com", "password": "pass123"})
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    
    # Usuario 2
    await async_client.post("/auth/register", json={"email": "user2@test.com", "password": "pass123", "full_name": "User 2"})
    login2 = await async_client.post("/auth/login", json={"email": "user2@test.com", "password": "pass123"})
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
    
    # User 1 crea lote
    create1 = await async_client.post("/lots", json={"name": "Lote User 1", "geometry": sample_polygon}, headers=headers1)
    lot_id = create1.json()["id"]
    
    # User 2 NO puede ver lote de user 1
    get_resp = await async_client.get(f"/lots/{lot_id}", headers=headers2)
    assert get_resp.status_code == 404
    
    # User 2 lista lotes - no debe ver lote de user 1
    list_resp = await async_client.get("/lots", headers=headers2)
    assert list_resp.json()["total"] == 0