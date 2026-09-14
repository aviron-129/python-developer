# Domain Entity & Schema for Service #01
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "FastAPI JWT Auth & Refresh Tokens"
    status: str = "active"
