# Domain Entity & Schema for Service #20
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Redis Cache-Aside & Write-Through"
    status: str = "active"
