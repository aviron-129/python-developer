# Domain Entity & Schema for Service #44
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Repository & Unit of Work Pattern"
    status: str = "active"
