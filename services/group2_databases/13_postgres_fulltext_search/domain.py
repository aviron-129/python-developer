# Domain Entity & Schema for Service #13
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "PostgreSQL Full-Text Search API"
    status: str = "active"
