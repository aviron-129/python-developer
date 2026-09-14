# Domain Entity & Schema for Service #50
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Decorator Pattern Cache & Telemetry"
    status: str = "active"
