from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.vehicle import VehicleCategory


class VehicleCreate(BaseModel):
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    category: VehicleCategory
    price: Decimal = Field(..., ge=0)
    quantity: int = Field(..., ge=0)


class VehicleUpdate(BaseModel):
    make: str | None = Field(None, min_length=1, max_length=100)
    model: str | None = Field(None, min_length=1, max_length=100)
    category: VehicleCategory | None = None
    price: Decimal | None = Field(None, ge=0)
    quantity: int | None = Field(None, ge=0)


class VehicleResponse(BaseModel):
    id: int
    make: str
    model: str
    category: VehicleCategory
    price: Decimal
    quantity: int

    model_config = {"from_attributes": True}


class RestockRequest(BaseModel):
    quantity: int = Field(..., gt=0)
