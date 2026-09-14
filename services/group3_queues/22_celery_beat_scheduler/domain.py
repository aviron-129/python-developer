# Domain Entity & Schema for Service #22
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Celery Beat Periodic Scheduler"
    status: str = "active"
