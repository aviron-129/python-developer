# Domain Entity & Schema for Service #27
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "FastAPI High-Performance Async REST API"
    status: str = "active"
