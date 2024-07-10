from pydantic import BaseModel

class ChainDTO(BaseModel):
    query: str