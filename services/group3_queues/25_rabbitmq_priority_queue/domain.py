# Domain Entity & Schema for Service #25
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "RabbitMQ Priority Queue Worker"
    status: str = "active"
