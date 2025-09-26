#!/usr/bin/env python3
"""
Pydantic-modeller för normaliserad Åland väderdata
Varje väderentitet har sin egen modell
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class Location(BaseModel):
    """Modell för en plats på Åland"""
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float

class Date(BaseModel):
    """Modell för datum med årstidsinformation"""
    id: Optional[int] = None
    date: date
    year: int
    month: int
    day: int
    day_of_year: int
    season: str

class Temperature(BaseModel):
    """Modell för temperaturdata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    temperature_c: float
    temperature_f: float
    feels_like_c: Optional[float] = None
    min_temperature_c: Optional[float] = None
    max_temperature_c: Optional[float] = None

class Humidity(BaseModel):
    """Modell för luftfuktighetsdata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    humidity_percent: int
    dew_point_c: Optional[float] = None

class Wind(BaseModel):
    """Modell för vinddata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    wind_speed_ms: float
    wind_speed_kmh: float
    wind_direction_degrees: float
    wind_direction_text: Optional[str] = None
    wind_gust_ms: Optional[float] = None

class Precipitation(BaseModel):
    """Modell för nederbördsdata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    precipitation_mm: float
    precipitation_inches: float
    precipitation_type: Optional[str] = None
    snow_depth_cm: Optional[float] = None

class Pressure(BaseModel):
    """Modell för lufttrycksdata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    pressure_hpa: float
    pressure_inhg: float
    pressure_trend: Optional[str] = None

class Visibility(BaseModel):
    """Modell för siktdata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    visibility_km: float
    visibility_miles: float
    fog_density: Optional[str] = None

class Cloudiness(BaseModel):
    """Modell för molnighetsdata"""
    id: Optional[int] = None
    date_id: int
    location_id: int
    cloudiness_percent: int
    cloud_type: Optional[str] = None
    cloud_height_m: Optional[float] = None

class WeatherRecordComplete(BaseModel):
    """Komplett väderdata-post med alla entiteter"""
    date: Date
    location: Location
    temperature: Temperature
    humidity: Humidity
    wind: Wind
    precipitation: Precipitation
    pressure: Pressure
    visibility: Visibility
    cloudiness: Cloudiness

class WeatherRecordSummary(BaseModel):
    """Sammanfattad väderdata-post"""
    date: date
    location_name: str
    temperature_c: float
    humidity_percent: int
    wind_speed_ms: float
    wind_direction_text: str
    precipitation_mm: float
    pressure_hpa: float
    visibility_km: float
    cloudiness_percent: int

class WeatherStats(BaseModel):
    """Statistik för väderdata"""
    total_records: int
    unique_locations: int
    date_range_start: date
    date_range_end: date
    temperature_stats: dict
    humidity_stats: dict
    wind_stats: dict
    precipitation_stats: dict
    pressure_stats: dict
    visibility_stats: dict
    cloudiness_stats: dict

class WeatherFilter(BaseModel):
    """Filter för väderdata-sökningar"""
    location_name: Optional[str] = None
    date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    season: Optional[str] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_humidity: Optional[int] = None
    max_humidity: Optional[int] = None
    min_wind_speed: Optional[float] = None
    max_wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    min_precipitation: Optional[float] = None
    max_precipitation: Optional[float] = None
    precipitation_type: Optional[str] = None
    min_pressure: Optional[float] = None
    max_pressure: Optional[float] = None
    min_visibility: Optional[float] = None
    max_visibility: Optional[float] = None
    fog_density: Optional[str] = None
    min_cloudiness: Optional[int] = None
    max_cloudiness: Optional[int] = None
    cloud_type: Optional[str] = None
    limit: Optional[int] = 100

class WeatherResponse(BaseModel):
    """Response-modell för väderdata-sökningar"""
    data: List[WeatherRecordSummary]
    count: int
    filters_applied: WeatherFilter

class LocationResponse(BaseModel):
    """Response-modell för platser"""
    locations: List[Location]
    count: int

class DateResponse(BaseModel):
    """Response-modell för datum"""
    dates: List[Date]
    count: int
    date_range_start: date
    date_range_end: date

class TableStatsResponse(BaseModel):
    """Response-modell för tabellstatistik"""
    table_stats: dict
    total_records: int
