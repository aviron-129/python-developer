# Domain Entity & Schema for Service #14
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Transaction Isolation Sandbox"
    status: str = "active"
