# Domain Entity & Schema for Service #42
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Crypto & Currency Monitor Bot"
    status: str = "active"
