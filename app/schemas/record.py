from pydantic import BaseModel


class RecordCreate(BaseModel):
    values: dict[int, str]


class RecordOut(BaseModel):
    id: int
    values: dict[int, str]

