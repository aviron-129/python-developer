# Domain Entity & Schema for Service #37
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Telegram Bot Celery Task Monitor"
    status: str = "active"
