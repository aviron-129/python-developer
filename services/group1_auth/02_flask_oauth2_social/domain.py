# Domain Entity & Schema for Service #02
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Flask OAuth2 Social Login"
    status: str = "active"
