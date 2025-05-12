from typing import Dict
from pydantic import BaseModel

class GameOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True

class ChipCoordsIn(BaseModel):
    idx: int
    left: float
    bottom: float

class ChipCoordsOut(BaseModel):
    coords: Dict[int, Dict[str, float]]
