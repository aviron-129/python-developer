# Domain Entity & Schema for Service #09
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Async SQLAlchemy 2.0 Engine & Session"
    status: str = "active"
