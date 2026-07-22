from decimal import Decimal

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.vehicle import Vehicle, VehicleCategory
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleService:
    """Business logic for vehicle CRUD and inventory management."""

    @staticmethod
    def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
        raise NotImplementedError

    @staticmethod
    def get_all_vehicles(db: Session) -> list[Vehicle]:
        raise NotImplementedError

    @staticmethod
    def search_vehicles(
        db: Session,
        make: str | None = None,
        model: str | None = None,
        category: VehicleCategory | None = None,
        price_min: Decimal | None = None,
        price_max: Decimal | None = None,
    ) -> list[Vehicle]:
        raise NotImplementedError

    @staticmethod
    def get_vehicle_or_404(db: Session, vehicle_id: int) -> Vehicle:
        raise NotImplementedError

    @staticmethod
    def update_vehicle(db: Session, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        raise NotImplementedError

    @staticmethod
    def delete_vehicle(db: Session, vehicle_id: int) -> None:
        raise NotImplementedError

    @staticmethod
    def purchase_vehicle(db: Session, vehicle_id: int) -> Vehicle:
        raise NotImplementedError

    @staticmethod
    def restock_vehicle(db: Session, vehicle_id: int, quantity: int) -> Vehicle:
        raise NotImplementedError
