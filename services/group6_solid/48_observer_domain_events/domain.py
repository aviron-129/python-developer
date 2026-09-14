# Domain Entity & Schema for Service #48
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Observer Pattern Event Dispatcher"
    status: str = "active"
