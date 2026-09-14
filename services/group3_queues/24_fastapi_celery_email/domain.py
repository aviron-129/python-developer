# Domain Entity & Schema for Service #24
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Async Email Dispatcher"
    status: str = "active"
