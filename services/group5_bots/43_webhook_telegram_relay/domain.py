# Domain Entity & Schema for Service #43
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Webhook-to-Telegram Messenger Relay"
    status: str = "active"
