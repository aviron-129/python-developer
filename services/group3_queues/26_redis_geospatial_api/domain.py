# Domain Entity & Schema for Service #26
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Redis Geospatial Proximity API"
    status: str = "active"
