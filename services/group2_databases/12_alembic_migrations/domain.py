# Domain Entity & Schema for Service #12
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Alembic Automated Migrations Engine"
    status: str = "active"
