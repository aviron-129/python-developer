# Domain Entity & Schema for Service #23
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Redis Redlock Distributed Manager"
    status: str = "active"
