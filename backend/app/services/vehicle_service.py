from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle, VehicleCategory
from app.schemas.vehicle import RestockRequest, VehicleCreate, VehicleUpdate


class VehicleService:
    """Business logic for vehicle CRUD and inventory management."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def get_vehicle_or_404(db: Session, vehicle_id: int) -> Vehicle:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found",
            )
        return vehicle

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
        vehicle = Vehicle(**data.model_dump())
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def get_all_vehicles(db: Session) -> list[Vehicle]:
        return db.query(Vehicle).order_by(Vehicle.id).all()

    @staticmethod
    def search_vehicles(
        db: Session,
        make: str | None = None,
        model: str | None = None,
        category: VehicleCategory | None = None,
        price_min: Decimal | None = None,
        price_max: Decimal | None = None,
    ) -> list[Vehicle]:
        query = db.query(Vehicle)

        if make:
            query = query.filter(Vehicle.make.ilike(f"%{make}%"))
        if model:
            query = query.filter(Vehicle.model.ilike(f"%{model}%"))
        if category:
            query = query.filter(Vehicle.category == category)
        if price_min is not None:
            query = query.filter(Vehicle.price >= price_min)
        if price_max is not None:
            query = query.filter(Vehicle.price <= price_max)

        return query.order_by(Vehicle.id).all()

    @staticmethod
    def update_vehicle(db: Session, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        vehicle = VehicleService.get_vehicle_or_404(db, vehicle_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return vehicle
        for field, value in update_data.items():
            setattr(vehicle, field, value)
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def delete_vehicle(db: Session, vehicle_id: int) -> None:
        vehicle = VehicleService.get_vehicle_or_404(db, vehicle_id)
        db.delete(vehicle)
        db.commit()

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    @staticmethod
    def purchase_vehicle(db: Session, vehicle_id: int) -> Vehicle:
        """Atomically decrement quantity by 1.
        Uses a single UPDATE … WHERE quantity > 0 RETURNING statement
        so concurrent requests cannot oversell.
        """
        result = db.execute(
            update(Vehicle)
            .where(Vehicle.id == vehicle_id, Vehicle.quantity > 0)
            .values(quantity=Vehicle.quantity - 1)
            .returning(Vehicle)
        )
        db.commit()
        vehicle = result.scalar_one_or_none()

        if not vehicle:
            # Vehicle may not exist, or it exists but quantity is 0
            exists = db.query(Vehicle.id).filter(Vehicle.id == vehicle_id).first()
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vehicle not found",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle is out of stock",
            )

        return vehicle

    @staticmethod
    def restock_vehicle(db: Session, vehicle_id: int, quantity: int) -> Vehicle:
        vehicle = VehicleService.get_vehicle_or_404(db, vehicle_id)
        vehicle.quantity += quantity
        db.commit()
        db.refresh(vehicle)
        return vehicle
