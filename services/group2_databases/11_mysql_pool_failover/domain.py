# Domain Entity & Schema for Service #11
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "MySQL Connection Pooling & Failover"
    status: str = "active"
