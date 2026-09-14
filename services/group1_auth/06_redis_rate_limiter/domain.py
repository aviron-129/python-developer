# Domain Entity & Schema for Service #06
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Redis API Rate Limiting Middleware"
    status: str = "active"
