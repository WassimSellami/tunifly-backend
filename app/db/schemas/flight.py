from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class FlightBase(BaseModel):
    departureDate: datetime
    price: float
    priceEur: float
    departureAirportCode: str
    arrivalAirportCode: str
    airlineCode: str


class FlightCreate(FlightBase):
    pass


class FlightUpdate(BaseModel):
    departureDate: Optional[datetime] = None
    price: Optional[float] = None
    priceEur: Optional[float] = None
    departureAirportCode: Optional[str] = None
    arrivalAirportCode: Optional[str] = None
    airlineCode: Optional[str] = None


class FlightOut(FlightBase):
    id: int
    isAvailable: bool
    bookingUrl: Optional[str] = None
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None

    class Config:
        from_attributes = True


class ScrapedFlight(BaseModel):
    departureDate: datetime
    price: float
    priceEur: float
    departureAirportCode: str
    arrivalAirportCode: str
    airlineCode: str


class ScrapedDataPayload(BaseModel):
    flights: List[ScrapedFlight]

    class Config:
        from_attributes = True
