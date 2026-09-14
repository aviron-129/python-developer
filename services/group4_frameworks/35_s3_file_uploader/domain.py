# Domain Entity & Schema for Service #35
from pydantic import BaseModel

class ServiceEntity(BaseModel):
    id: int
    name: str = "S3 / MinIO Async File Upload Manager"
    status: str = "active"
