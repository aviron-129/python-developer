# Domain Entity & Schema for Service #16
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "SQLAlchemy Soft Delete & Audit Log"
    status: str = "active"
