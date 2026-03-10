from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class FieldCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    field_type: str = Field(default="text")


class FieldOut(BaseModel):
    id: int
    display_name: str
    internal_name: str
    field_type: str

    model_config = {"from_attributes": True}

