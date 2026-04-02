from pydantic import BaseModel, Field

class RecordBase(BaseModel):
    amount: float
    type: str = Field(..., pattern="^(income|expense)$")
    category: str | None = None
    date: str | None = None
    notes: str | None = None

class RecordCreate(RecordBase):
    pass

class RecordUpdate(BaseModel):
    amount: float | None = None
    type: str | None = Field(None, pattern="^(income|expense)$")
    category: str | None = None
    date: str | None = None
    notes: str | None = None

class RecordResponse(RecordBase):
    id: int
    user_id: int
    deleted_at: str | None = None
