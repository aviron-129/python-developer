# Domain Entity & Schema for Service #52
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "pytest Integration & Unit Test Suite"
    status: str = "active"
