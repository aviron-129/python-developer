# Domain Entity & Schema for Service #04
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Redis JWT Blacklist & Logout"
    status: str = "active"
