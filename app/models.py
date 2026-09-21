"""Pydantic schemas for request/response validation."""
from typing import Optional

from pydantic import BaseModel, Field


class PersonIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    dob: Optional[str] = None  # YYYY-MM-DD
    dod: Optional[str] = None  # YYYY-MM-DD
    gender: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class RelationshipIn(BaseModel):
    person_a_id: int
    person_b_id: int
    relationship_type: str  # 'parent' or 'spouse'


class ReminderIn(BaseModel):
    person_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    reminder_date: str  # YYYY-MM-DD
    repeat_yearly: bool = True
    notes: Optional[str] = None
