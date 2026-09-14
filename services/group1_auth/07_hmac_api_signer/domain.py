# Domain Entity & Schema for Service #07
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "HMAC Request Signer & Replay Guard"
    status: str = "active"
