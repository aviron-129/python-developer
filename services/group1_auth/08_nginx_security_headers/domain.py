# Domain Entity & Schema for Service #08
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Nginx OWASP Security Headers Guard"
    status: str = "active"
