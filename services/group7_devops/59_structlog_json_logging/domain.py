# Domain Entity & Schema for Service #59
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Structured JSON Logging Microservice"
    status: str = "active"
