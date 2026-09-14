# Domain Entity & Schema for Service #03
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Django DRF RBAC & Custom Claims"
    status: str = "active"
