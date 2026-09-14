# Domain Entity & Schema for Service #56
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "GitHub Actions CI/CD Pipeline"
    status: str = "active"
