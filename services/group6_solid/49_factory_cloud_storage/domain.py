# Domain Entity & Schema for Service #49
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Abstract Factory Storage Driver"
    status: str = "active"
