# Domain Entity & Schema for Service #15
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Django Multi-DB Router & Replicas"
    status: str = "active"
