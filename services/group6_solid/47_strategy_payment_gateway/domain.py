# Domain Entity & Schema for Service #47
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Strategy Pattern Payment Processor"
    status: str = "active"
