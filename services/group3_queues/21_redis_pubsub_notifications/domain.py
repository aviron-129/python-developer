# Domain Entity & Schema for Service #21
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Redis Pub/Sub Notification Service"
    status: str = "active"
