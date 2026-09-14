# Domain Entity & Schema for Service #46
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "CQRS Command Query Segregation Engine"
    status: str = "active"
