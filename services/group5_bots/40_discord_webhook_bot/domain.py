# Domain Entity & Schema for Service #40
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Discord Metric Notification Bot"
    status: str = "active"
