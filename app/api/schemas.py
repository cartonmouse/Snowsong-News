from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str = Field(default="", max_length=200)


class SubscriptionUpdate(BaseModel):
    topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    push_channel: str = Field(default="history", max_length=100)

