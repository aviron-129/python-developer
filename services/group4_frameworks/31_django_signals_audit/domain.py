# Domain Entity & Schema for Service #31
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Django Signals Audit Logging"
    status: str = "active"
