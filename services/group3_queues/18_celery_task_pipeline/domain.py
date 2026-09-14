# Domain Entity & Schema for Service #18
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Celery Distributed Workflow Pipeline"
    status: str = "active"
