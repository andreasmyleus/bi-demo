#!/usr/bin/env python3
"""
FastAPI-applikation för Åland väderdata
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import pandas as pd
import json
from typing import Optional, List
from datetime import datetime
import os

app = FastAPI(
    title="Åland Väderdata API",
    description="API för att hämta väderdata från olika platser på Åland",
    version="1.0.0"
)

# Ladda data vid start
weather_data = None

@app.on_event("startup")
async def load_data():
    """Ladda väderdata vid applikationsstart"""
    global weather_data
    try:
        weather_data = pd.read_csv('aland_weather_data.csv')
        print(f"Laddat {len(weather_data)} väderdata-poster")
    except FileNotFoundError:
        print("Varning: aland_weather_data.csv hittades inte")
        weather_data = pd.DataFrame()

@app.get("/")
async def root():
    """Root endpoint med API-information"""
    return {
        "message": "Åland Väderdata API",
        "version": "1.0.0",
        "endpoints": {
            "/weather": "Hämta all väderdata",
            "/weather/locations": "Hämta lista över platser",
            "/weather/dates": "Hämta lista över datum",
            "/weather/stats": "Hämta statistik"
        }
    }

@app.get("/weather")
async def get_weather_data(
    location: Optional[str] = Query(None, description="Filtrera på plats"),
    date: Optional[str] = Query(None, description="Filtrera på datum (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Startdatum för intervall (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Slutdatum för intervall (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Max antal rader att returnera")
):
    """
    Hämta väderdata med valfria filter
    """
    if weather_data is None or weather_data.empty:
        raise HTTPException(status_code=500, detail="Väderdata är inte tillgänglig")
    
    # Kopiera data för filtrering
    filtered_data = weather_data.copy()
    
    # Filtrera på plats
    if location:
        filtered_data = filtered_data[filtered_data['plats'].str.contains(location, case=False, na=False)]
    
    # Filtrera på specifikt datum
    if date:
        filtered_data = filtered_data[filtered_data['datum'] == date]
    
    # Filtrera på datumintervall
    if start_date:
        filtered_data = filtered_data[filtered_data['datum'] >= start_date]
    if end_date:
        filtered_data = filtered_data[filtered_data['datum'] <= end_date]
    
    # Begränsa antal rader
    if limit:
        filtered_data = filtered_data.head(limit)
    
    # Konvertera till JSON-format
    result = filtered_data.to_dict('records')
    
    return {
        "data": result,
        "count": len(result),
        "filters_applied": {
            "location": location,
            "date": date,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
    }

@app.get("/weather/locations")
async def get_locations():
    """Hämta lista över alla platser"""
    if weather_data is None or weather_data.empty:
        raise HTTPException(status_code=500, detail="Väderdata är inte tillgänglig")
    
    locations = weather_data[['plats', 'latitud', 'longitud']].drop_duplicates().to_dict('records')
    
    return {
        "locations": locations,
        "count": len(locations)
    }

@app.get("/weather/dates")
async def get_dates():
    """Hämta lista över alla datum"""
    if weather_data is None or weather_data.empty:
        raise HTTPException(status_code=500, detail="Väderdata är inte tillgänglig")
    
    dates = sorted(weather_data['datum'].unique().tolist())
    
    return {
        "dates": dates,
        "count": len(dates),
        "date_range": {
            "start": dates[0] if dates else None,
            "end": dates[-1] if dates else None
        }
    }

@app.get("/weather/stats")
async def get_weather_stats():
    """Hämta statistik över väderdata"""
    if weather_data is None or weather_data.empty:
        raise HTTPException(status_code=500, detail="Väderdata är inte tillgänglig")
    
    stats = {
        "total_records": len(weather_data),
        "unique_locations": weather_data['plats'].nunique(),
        "date_range": {
            "start": weather_data['datum'].min(),
            "end": weather_data['datum'].max()
        },
        "temperature": {
            "min": float(weather_data['temperatur_c'].min()),
            "max": float(weather_data['temperatur_c'].max()),
            "avg": round(float(weather_data['temperatur_c'].mean()), 2)
        },
        "humidity": {
            "min": float(weather_data['luftfuktighet_procent'].min()),
            "max": float(weather_data['luftfuktighet_procent'].max()),
            "avg": round(float(weather_data['luftfuktighet_procent'].mean()), 2)
        },
        "precipitation": {
            "total": round(float(weather_data['nederbord_mm'].sum()), 2),
            "max_daily": round(float(weather_data['nederbord_mm'].max()), 2),
            "avg": round(float(weather_data['nederbord_mm'].mean()), 2)
        }
    }
    
    return stats

@app.get("/weather/location/{location_name}")
async def get_weather_by_location(location_name: str):
    """Hämta väderdata för en specifik plats"""
    if weather_data is None or weather_data.empty:
        raise HTTPException(status_code=500, detail="Väderdata är inte tillgänglig")
    
    location_data = weather_data[weather_data['plats'].str.contains(location_name, case=False, na=False)]
    
    if location_data.empty:
        raise HTTPException(status_code=404, detail=f"Plats '{location_name}' hittades inte")
    
    result = location_data.to_dict('records')
    
    return {
        "location": location_name,
        "data": result,
        "count": len(result)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

