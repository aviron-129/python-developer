# Domain Entity & Schema for Service #53
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Docker Multi-Stage Build Optimization"
    status: str = "active"
