# Domain Entity & Schema for Service #41
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "RSS News Aggregator Bot"
    status: str = "active"
