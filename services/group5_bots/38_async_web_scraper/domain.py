# Domain Entity & Schema for Service #38
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Async Web Scraper Pipeline"
    status: str = "active"
