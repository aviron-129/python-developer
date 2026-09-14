# Domain Entity & Schema for Service #55
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Nginx Reverse Proxy & SSL Termination"
    status: str = "active"
