# Domain Entity & Schema for Service #51
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Clean Onion Layer Architecture"
    status: str = "active"
