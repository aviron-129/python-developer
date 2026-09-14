# Domain Entity & Schema for Service #33
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Async Webhook Receiver with Retries"
    status: str = "active"
