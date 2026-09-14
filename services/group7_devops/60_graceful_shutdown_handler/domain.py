# Domain Entity & Schema for Service #60
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Graceful Shutdown Orchestrator"
    status: str = "active"
