# Domain Entity & Schema for Service #34
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Dynamic PDF & Excel Exporter"
    status: str = "active"
