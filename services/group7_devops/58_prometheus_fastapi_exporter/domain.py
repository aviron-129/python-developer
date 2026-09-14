# Domain Entity & Schema for Service #58
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Prometheus Metrics Exporter"
    status: str = "active"
