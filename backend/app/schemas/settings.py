from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class CenterCreate(BaseModel):
    name: str = Field(..., max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=20)
    opened_at: Optional[date] = None


class CenterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=20)
    opened_at: Optional[date] = None


class ZoneCreate(BaseModel):
    center_id: int
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)


class LineCreate(BaseModel):
    center_id: int
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    rail_length_m: float
    section_count: int


class SectionCreate(BaseModel):
    line_id: int
    name: Optional[str] = Field(None, max_length=100)
    order_in_line: Optional[int] = None
    type: Optional[str] = Field(None, max_length=50)


class SensorCreate(BaseModel):
    section_id: int
    equipment_id: Optional[int] = None
    sensor_type: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)


class ThresholdUpdate(BaseModel):
    config_value: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=200)
