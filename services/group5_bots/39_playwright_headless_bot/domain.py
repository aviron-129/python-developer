# Domain Entity & Schema for Service #39
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Playwright Headless Automation Bot"
    status: str = "active"
