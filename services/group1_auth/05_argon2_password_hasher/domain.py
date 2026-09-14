# Domain Entity & Schema for Service #05
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "Argon2id & Bcrypt Hasher Benchmark"
    status: str = "active"
