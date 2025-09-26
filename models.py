#!/usr/bin/env python3
"""
Pydantic-modeller för Åland väderdata
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class Location(BaseModel):
    """Modell för en plats på Åland"""
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float

class WeatherRecord(BaseModel):
    """Modell för en väderdata-post"""
    id: Optional[int] = None
    date: date
    location_id: int
    temperature_c: float
    humidity_percent: int
    wind_speed_ms: float
    wind_direction_degrees: float
    precipitation_mm: float
    pressure_hpa: float
    visibility_km: float
    cloudiness_percent: int

class WeatherRecordWithLocation(WeatherRecord):
    """Väderdata-post med platsinformation inkluderad"""
    location: Location

class WeatherStats(BaseModel):
    """Statistik för väderdata"""
    total_records: int
    unique_locations: int
    date_range_start: date
    date_range_end: date
    temperature_min: float
    temperature_max: float
    temperature_avg: float
    humidity_min: int
    humidity_max: int
    humidity_avg: float
    precipitation_total: float
    precipitation_max_daily: float
    precipitation_avg: float

class WeatherFilter(BaseModel):
    """Filter för väderdata-sökningar"""
    location_name: Optional[str] = None
    date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_humidity: Optional[int] = None
    max_humidity: Optional[int] = None
    min_precipitation: Optional[float] = None
    max_precipitation: Optional[float] = None
    limit: Optional[int] = 100

class WeatherResponse(BaseModel):
    """Response-modell för väderdata-sökningar"""
    data: List[WeatherRecordWithLocation]
    count: int
    filters_applied: WeatherFilter

class LocationResponse(BaseModel):
    """Response-modell för platser"""
    locations: List[Location]
    count: int

class DateResponse(BaseModel):
    """Response-modell för datum"""
    dates: List[date]
    count: int
    date_range_start: date
    date_range_end: date
