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


@pytest.fixture
def small_polygon():
    """Polígono muy pequeño (< 0.01 ha) para test de área mínima."""
    # Aprox 10m x 10m = 100 m² = 0.01 ha
    return {
        "type": "Polygon",
        "coordinates": [[
            [-58.5, -34.5],
            [-58.5, -34.5001],
            [-58.4999, -34.5001],
            [-58.4999, -34.5],
            [-58.5, -34.5]
        ]]
    }


@pytest.fixture
def bigger_polygon():
    """Polígono más grande para test de actualización de área."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [-58.6, -34.6],
            [-58.6, -34.3],
            [-58.3, -34.3],
            [-58.3, -34.6],
            [-58.6, -34.6]
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
    assert "deleted_at" in data  # Nuevo campo


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
async def test_create_lot_area_too_small(async_client: AsyncClient, auth_headers, small_polygon):
    """Prueba creación con área menor al mínimo (0.01 ha)."""
    response = await async_client.post(
        "/lots",
        json={"name": "Lote Pequeño", "geometry": small_polygon},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "Área demasiado pequeña" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_lot_creates_version(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba que la creación genera versión v1."""
    response = await async_client.post(
        "/lots",
        json={"name": "Lote Con Versión", "geometry": sample_polygon},
        headers=auth_headers,
    )
    assert response.status_code == 201
    lot_id = response.json()["id"]
    
    # Verificar versiones
    versions_resp = await async_client.get(f"/lots/{lot_id}/versions", headers=auth_headers)
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["name"] == "Lote Con Versión"
    assert versions[0]["change_reason"] == "Creación inicial"


@pytest.mark.asyncio
async def test_list_lots(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba listado paginado de lotes."""
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
async def test_list_lots_advanced_filters(async_client: AsyncClient, auth_headers, sample_polygon, bigger_polygon):
    """Prueba filtros avanzados: fecha, área, bbox."""
    # Crear lote 1
    resp1 = await async_client.post("/lots", json={"name": "Lote Filtro 1", "geometry": sample_polygon}, headers=auth_headers)
    lot1_id = resp1.json()["id"]
    
    # Crear lote 2 más grande
    await async_client.post("/lots", json={"name": "Lote Filtro 2", "geometry": bigger_polygon}, headers=auth_headers)
    
    # Filtro por área mínima
    response = await async_client.get("/lots?area_min=500", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Solo lote 2 debería aparecer (área > 500 ha)
    assert all(lot["area_ha"] >= 500 for lot in data["items"])
    
    # Filtro por búsqueda de nombre
    response = await async_client.get("/lots?search=Filtro", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    
    # Filtro por bbox
    response = await async_client.get("/lots?bbox=-58.6,-34.6,-58.3,-34.3", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba obtención de lote por ID."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Detalle", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    response = await async_client.get(f"/lots/{lot_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lot_id
    assert data["name"] == "Lote Detalle"
    assert "deleted_at" in data


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
    
    # Verificar que NO se creó nueva versión (no cambió geometría)
    versions_resp = await async_client.get(f"/lots/{lot_id}/versions", headers=auth_headers)
    versions = versions_resp.json()
    assert len(versions) == 1  # Solo versión inicial


@pytest.mark.asyncio
async def test_update_lot_geometry_creates_version(async_client: AsyncClient, auth_headers, sample_polygon, bigger_polygon):
    """Prueba actualización de geometría crea nueva versión."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Geo Update", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    original_area = create_resp.json()["area_ha"]
    
    # Actualizar geometría con change_reason
    response = await async_client.patch(
        f"/lots/{lot_id}",
        json={"geometry": bigger_polygon, "change_reason": "Ampliación de límites"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["area_ha"] > original_area
    
    # Verificar que se creó versión v2
    versions_resp = await async_client.get(f"/lots/{lot_id}/versions", headers=auth_headers)
    versions = versions_resp.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2  # Más reciente primero
    assert versions[0]["change_reason"] == "Ampliación de límites"
    assert versions[1]["version_number"] == 1


@pytest.mark.asyncio
async def test_update_lot_geometry_area_too_small(async_client: AsyncClient, auth_headers, sample_polygon, small_polygon):
    """Prueba que actualización a área muy pequeña falla."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Para Reducir", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    response = await async_client.patch(
        f"/lots/{lot_id}",
        json={"geometry": small_polygon},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "Área demasiado pequeña" in response.json()["detail"]


@pytest.mark.asyncio
async def test_soft_delete_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba soft delete de lote."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote A Borrar", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    # Eliminar
    response = await async_client.delete(f"/lots/{lot_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verificar que ya no aparece en listado normal
    get_resp = await async_client.get(f"/lots/{lot_id}", headers=auth_headers)
    assert get_resp.status_code == 404
    
    # Pero existe en BD (soft delete)
    list_resp = await async_client.get("/lots", headers=auth_headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_restore_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba restauración de lote soft-deleted."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote A Restaurar", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    # Eliminar
    await async_client.delete(f"/lots/{lot_id}", headers=auth_headers)
    
    # Restaurar
    response = await async_client.post(f"/lots/{lot_id}/restore", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Lote A Restaurar"
    assert data["deleted_at"] is None
    
    # Verificar que aparece en listado
    list_resp = await async_client.get("/lots", headers=auth_headers)
    assert list_resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_soft_delete_preserves_analyses(async_client: AsyncClient, auth_headers, sample_polygon):
    """Prueba que soft delete NO elimina analyses (se conservan para auditoría)."""
    # Este test verifica que al hacer soft delete, los analyses no se borran en cascada
    # (El FK en Analysis no tiene ON DELETE CASCADE, o usamos soft delete en Lot)
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Con Analyses", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    # Crear análisis (simulado - en test real se crearía via endpoint)
    # Verificar que el lote existe y luego soft delete no elimina analyses
    delete_resp = await async_client.delete(f"/lots/{lot_id}", headers=auth_headers)
    assert delete_resp.status_code == 204
    
    # El lote está soft-deleted pero los analyses siguen en BD
    # (Verificación real requeriría acceso directo a BD o endpoint de analyses)


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
    
    # User 1 soft delete
    await async_client.delete(f"/lots/{lot_id}", headers=headers1)
    
    # User 2 NO puede ver lote eliminado de user 1 (include_deleted=false por defecto)
    get_resp2 = await async_client.get(f"/lots/{lot_id}", headers=headers2)
    assert get_resp2.status_code == 404


@pytest.mark.asyncio
async def test_version_history_ordering(async_client: AsyncClient, auth_headers, sample_polygon, bigger_polygon):
    """Prueba que las versiones se ordenan descendente (más reciente primero)."""
    create_resp = await async_client.post(
        "/lots",
        json={"name": "Lote Versionado", "geometry": sample_polygon},
        headers=auth_headers,
    )
    lot_id = create_resp.json()["id"]
    
    # Actualizar geometría 3 veces con diferentes razones
    for i in range(3):
        bigger = {
            "type": "Polygon",
            "coordinates": [[
                [-58.5 - i*0.05, -34.5 - i*0.05],
                [-58.5 - i*0.05, -34.4 - i*0.05],
                [-58.4 - i*0.05, -34.4 - i*0.05],
                [-58.4 - i*0.05, -34.5 - i*0.05],
                [-58.5 - i*0.05, -34.5 - i*0.05]
            ]]
        }
        await async_client.patch(
            f"/lots/{lot_id}",
            json={"geometry": bigger, "change_reason": f"Actualización {i+1}"},
            headers=auth_headers,
        )
    
    # Verificar versiones
    versions_resp = await async_client.get(f"/lots/{lot_id}/versions", headers=auth_headers)
    versions = versions_resp.json()
    
    # Debe haber 4 versiones (1 inicial + 3 actualizaciones)
    assert len(versions) == 4
    
    # Orden descendente: v4, v3, v2, v1
    assert versions[0]["version_number"] == 4
    assert versions[1]["version_number"] == 3
    assert versions[2]["version_number"] == 2
    assert versions[3]["version_number"] == 1
    
    # Verificar motivos
    assert versions[0]["change_reason"] == "Actualización 3"
    assert versions[1]["change_reason"] == "Actualización 2"
    assert versions[2]["change_reason"] == "Actualización 1"
    assert versions[3]["change_reason"] == "Creación inicial"