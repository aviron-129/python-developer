# Domain Entity & Schema for Service #54
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Multi-Container Docker Compose Stack"
    status: str = "active"
