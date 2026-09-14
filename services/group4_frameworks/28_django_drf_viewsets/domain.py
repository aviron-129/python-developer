# Domain Entity & Schema for Service #28
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Django DRF ViewSets & Filtering"
    status: str = "active"
