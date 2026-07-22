from fastapi import APIRouter

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("")
async def list_vehicles():
    raise NotImplementedError


@router.get("/search")
async def search_vehicles():
    raise NotImplementedError


@router.post("", status_code=201)
async def create_vehicle():
    raise NotImplementedError


@router.put("/{vehicle_id}")
async def update_vehicle(vehicle_id: int):
    raise NotImplementedError


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(vehicle_id: int):
    raise NotImplementedError


@router.post("/{vehicle_id}/purchase")
async def purchase_vehicle(vehicle_id: int):
    raise NotImplementedError


@router.post("/{vehicle_id}/restock")
async def restock_vehicle(vehicle_id: int):
    raise NotImplementedError
