from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.models.vehicle import VehicleCategory
from app.schemas.vehicle import (
    RestockRequest,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


# ---------------------------------------------------------------------------
# GET /api/vehicles — list all vehicles (authenticated)
# ---------------------------------------------------------------------------
@router.get("")
async def list_vehicles(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    vehicles = VehicleService.get_all_vehicles(db)
    return [VehicleResponse.model_validate(v) for v in vehicles]


# ---------------------------------------------------------------------------
# GET /api/vehicles/search — search vehicles (authenticated)
# ---------------------------------------------------------------------------
@router.get("/search")
async def search_vehicles(
    make: str | None = Query(None),
    model: str | None = Query(None),
    category: VehicleCategory | None = Query(None),
    price_min: Decimal | None = Query(None),
    price_max: Decimal | None = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    vehicles = VehicleService.search_vehicles(
        db, make=make, model=model, category=category,
        price_min=price_min, price_max=price_max,
    )
    return [VehicleResponse.model_validate(v) for v in vehicles]


# ---------------------------------------------------------------------------
# POST /api/vehicles — create vehicle (admin only)
# ---------------------------------------------------------------------------
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    body: VehicleCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    vehicle = VehicleService.create_vehicle(db, body)
    return VehicleResponse.model_validate(vehicle)


# ---------------------------------------------------------------------------
# PUT /api/vehicles/{vehicle_id} — update vehicle (admin only)
# ---------------------------------------------------------------------------
@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    body: VehicleUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    vehicle = VehicleService.update_vehicle(db, vehicle_id, body)
    return VehicleResponse.model_validate(vehicle)


# ---------------------------------------------------------------------------
# DELETE /api/vehicles/{vehicle_id} — delete vehicle (admin only)
# ---------------------------------------------------------------------------
@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    VehicleService.delete_vehicle(db, vehicle_id)


# ---------------------------------------------------------------------------
# POST /api/vehicles/{vehicle_id}/purchase — purchase (authenticated)
# ---------------------------------------------------------------------------
@router.post("/{vehicle_id}/purchase")
async def purchase_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    vehicle = VehicleService.purchase_vehicle(db, vehicle_id)
    return VehicleResponse.model_validate(vehicle)


# ---------------------------------------------------------------------------
# POST /api/vehicles/{vehicle_id}/restock — restock (admin only)
# ---------------------------------------------------------------------------
@router.post("/{vehicle_id}/restock")
async def restock_vehicle(
    vehicle_id: int,
    body: RestockRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    vehicle = VehicleService.restock_vehicle(db, vehicle_id, body.quantity)
    return VehicleResponse.model_validate(vehicle)
