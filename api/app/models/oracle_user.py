"""Pydantic models for Oracle user CRUD endpoints."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OracleUserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    name_persian: str | None = Field(None, max_length=200)
    birthday: date
    mother_name: str = Field(..., min_length=1, max_length=200)
    mother_name_persian: str | None = Field(None, max_length=200)
    country: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)

    @field_validator("birthday")
    @classmethod
    def birthday_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Birthday cannot be in the future")
        return v


class OracleUserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    name_persian: str | None = Field(None, max_length=200)
    birthday: date | None = None
    mother_name: str | None = Field(None, min_length=1, max_length=200)
    mother_name_persian: str | None = Field(None, max_length=200)
    country: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)

    @field_validator("birthday")
    @classmethod
    def birthday_not_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("Birthday cannot be in the future")
        return v


class OracleUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_persian: str | None = None
    birthday: date
    mother_name: str
    mother_name_persian: str | None = None
    country: str | None = None
    city: str | None = None
    created_at: datetime
    updated_at: datetime


class OracleUserListResponse(BaseModel):
    users: list[OracleUserResponse]
    total: int
    limit: int
    offset: int
