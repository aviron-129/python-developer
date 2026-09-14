# Domain Entity & Schema for Service #17
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "High-Speed PostgreSQL COPY Seeder"
    status: str = "active"
