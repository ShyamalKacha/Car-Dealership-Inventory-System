import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VehicleCategory(str, enum.Enum):
    SUV = "SUV"
    SEDAN = "SEDAN"
    TRUCK = "TRUCK"
    COUPE = "COUPE"
    HATCHBACK = "HATCHBACK"
    VAN = "VAN"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    make: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[VehicleCategory] = mapped_column(
        Enum(VehicleCategory), nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
