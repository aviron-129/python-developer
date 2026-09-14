# Domain Entity & Schema for Service #30
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "FastAPI Server-Sent Events Stream"
    status: str = "active"
