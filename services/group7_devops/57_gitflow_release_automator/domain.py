# Domain Entity & Schema for Service #57
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "GitFlow Release & SemVer Automator"
    status: str = "active"
