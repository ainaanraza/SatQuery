from pydantic import BaseModel

class GeoEntity(BaseModel):
    entity_id: str
    name: str
    geometry: dict
    crs: str
    source: str
    confidence: float
