# Domain Entity & Schema for Service #45
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Dependency Inversion Container (DIP)"
    status: str = "active"
