# Tests de análisis raster - pytest-asyncio
import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.main import app
from app.models.user import User
from app.models.lot import Lot
from app.models.analysis import Analysis, ResourceType, AnalysisStatus
from app.core.security import hash_password
from app.services.raster_service import _compute_geometry_hash


@pytest.fixture
async def test_user(async_client: AsyncClient):
    """Crea un usuario de prueba y retorna sus credenciales + token."""
    # Registrar
    reg_response = await async_client.post(
        "/auth/register",
        json={"email": "rastertest@example.com", "password": "password123", "full_name": "Raster Test User"},
    )
    assert reg_response.status_code == 201
    
    # Login
    login_response = await async_client.post(
        "/auth/login",
        json={"email": "rastertest@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    return {"tokens": tokens, "email": "rastertest@example.com"}


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
async def test_lot(async_client: AsyncClient, auth_headers, sample_polygon):
    """Crea un lote de prueba."""
    response = await async_client.post(
        "/lots",
        json={"name": "Lote Raster Test", "geometry": sample_polygon},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_analysis(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba creación de análisis con versionado."""
    response = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1", "store_clipped_raster": False},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["lot_id"] == test_lot["id"]
    assert data["resource_type"] == "resource_1"
    assert data["status"] == "pending"
    assert "raster_version" in data
    assert "raster_date" in data
    assert "lot_geometry_hash" in data
    assert "store_clipped_raster" in data


@pytest.mark.asyncio
async def test_create_analysis_checks_concurrency(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba que se rechace análisis concurrente para mismo lote+recurso."""
    # Crear primer análisis
    resp1 = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1"},
        headers=auth_headers,
    )
    assert resp1.status_code == 202
    analysis1_id = resp1.json()["id"]
    
    # Intentar crear segundo análisis simultáneo para mismo lote+recurso
    resp2 = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1"},
        headers=auth_headers,
    )
    assert resp2.status_code == 409
    error_data = resp2.json()
    assert "Ya existe un análisis en curso" in error_data["detail"]["error"]
    assert "existing_analysis_id" in error_data["detail"]
    assert "retry_after_seconds" in error_data["detail"]


@pytest.mark.asyncio
async def test_check_analysis_cache(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba endpoint de verificación de cache."""
    # Verificar cache (debe estar vacío)
    response = await async_client.post(
        "/analyses/check-cache",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cached"] == False
    assert data["analysis"] is None


@pytest.mark.asyncio
async def test_analysis_versioning(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba que el análisis guarda versión de raster y fecha."""
    response = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1", "store_clipped_raster": False},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    
    # Verificar campos de versionado
    assert "raster_version" in data
    assert data["raster_version"] is not None
    assert data["raster_version"].startswith("v")
    assert "raster_date" in data
    assert data["raster_date"] is not None


@pytest.mark.asyncio
async def test_analysis_store_clipped_raster(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba opción de almacenar raster recortado."""
    response = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1", "store_clipped_raster": True},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["store_clipped_raster"] == True


@pytest.mark.asyncio
async def test_analysis_geometry_hash(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba que se guarda hash de geometría para cache."""
    response = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1"},
        headers=auth_headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert "lot_geometry_hash" in data
    assert len(data["lot_geometry_hash"]) == 64  # SHA256 hex


@pytest.mark.asyncio
async def test_list_analyses_with_filters(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba listado con filtros avanzados."""
    # Crear un análisis
    await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1"},
        headers=auth_headers,
    )
    
    # Filtro por status
    response = await async_client.get("/analyses?status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(a["status"] == "pending" for a in data["items"])
    
    # Filtro por resource_type
    response = await async_client.get("/analyses?resource_type=resource_1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(a["resource_type"] == "resource_1" for a in data["items"])


@pytest.mark.asyncio
async def test_get_analysis_detail(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba obtención de detalle de análisis con versionado."""
    create_resp = await async_client.post(
        "/analyses",
        json={"lot_id": test_lot["id"], "resource_type": "resource_1"},
        headers=auth_headers,
    )
    analysis_id = create_resp.json()["id"]
    
    response = await async_client.get(f"/analyses/{analysis_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verificar campos de versionado en detalle
    assert "raster_version" in data
    assert "raster_date" in data
    assert "lot_geometry_hash" in data
    assert "store_clipped_raster" in data
    assert "clipped_raster_path" in data


@pytest.mark.asyncio
async def test_get_lot_analyses(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba shortcut para análisis de un lote."""
    response = await async_client.get(f"/lots/{test_lot['id']}/analyses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_analysis_timeseries(async_client: AsyncClient, auth_headers, test_lot):
    """Prueba endpoint de serie temporal con versionado."""
    response = await async_client.get(
        f"/analyses/timeseries?lot_id={test_lot['id']}&resource_type=resource_1",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "lot_id" in data
    assert "resource_type" in data
    assert "data" in data
    # Verificar que cada punto tiene versionado
    for point in data["data"]:
        assert "analyzed_at" in point
        assert "average_rate" in point
        assert "resource_type" in point


@pytest.mark.asyncio
async def test_analysis_ownership_isolation(async_client: AsyncClient, sample_polygon):
    """Prueba que usuarios solo ven sus propios análisis."""
    # Usuario 1
    await async_client.post("/auth/register", json={"email": "u1@test.com", "password": "pass123", "full_name": "User 1"})
    login1 = await async_client.post("/auth/login", json={"email": "u1@test.com", "password": "pass123"})
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    
    # Usuario 2
    await async_client.post("/auth/register", json={"email": "u2@test.com", "password": "pass123", "full_name": "User 2"})
    login2 = await async_client.post("/auth/login", json={"email": "u2@test.com", "password": "pass123"})
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
    
    # User 1 crea lote
    lot1 = await async_client.post("/lots", json={"name": "Lote User 1", "geometry": sample_polygon}, headers=headers1)
    lot_id = lot1.json()["id"]
    
    # User 1 crea análisis
    await async_client.post("/analyses", json={"lot_id": lot_id, "resource_type": "resource_1"}, headers=headers1)
    
    # User 2 NO puede ver análisis de user 1
    get_resp = await async_client.get(f"/lots/{lot_id}/analyses", headers=headers2)
    assert get_resp.status_code == 404
    
    # User 2 lista análisis - no debe ver de user 1
    list_resp = await async_client.get("/analyses", headers=headers2)
    assert list_resp.json()["total"] == 0