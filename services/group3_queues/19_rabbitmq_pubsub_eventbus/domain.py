# Domain Entity & Schema for Service #19
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "RabbitMQ Event Bus & DLQ Handler"
    status: str = "active"
