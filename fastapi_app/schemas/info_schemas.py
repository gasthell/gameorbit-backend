from pydantic import BaseModel

class InfoOut(BaseModel):
    name: str
    description: str
