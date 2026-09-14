# Domain Entity & Schema for Service #36
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "aiogram 3.x Async Telegram Bot"
    status: str = "active"
