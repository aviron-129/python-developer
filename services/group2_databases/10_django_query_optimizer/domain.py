# Domain Entity & Schema for Service #10
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Django ORM Query Optimizer & N+1"
    status: str = "active"
