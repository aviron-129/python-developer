# Domain Entity & Schema for Service #32
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Strawberry GraphQL Microservice"
    status: str = "active"
