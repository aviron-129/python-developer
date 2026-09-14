# Domain Entity & Schema for Service #29
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Flask Modular Blueprints Service"
    status: str = "active"
