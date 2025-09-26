#!/usr/bin/env python3
"""
SQLite-databas för Åland väderdata
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import Location, WeatherRecord, WeatherRecordWithLocation
import requests
import json

class WeatherDatabase:
    """Hanterar SQLite-databas för väderdata"""
    
    def __init__(self, db_path: str = "weather.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Anslut till databasen"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Gör att vi kan komma åt kolumner som dict-nycklar
        return self.conn
    
    def close(self):
        """Stäng databasanslutningen"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Skapa tabeller i databasen"""
        cursor = self.conn.cursor()
        
        # Tabell för platser
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabell för väderdata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                location_id INTEGER NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_percent INTEGER NOT NULL,
                wind_speed_ms REAL NOT NULL,
                wind_direction_degrees REAL NOT NULL,
                precipitation_mm REAL NOT NULL,
                pressure_hpa REAL NOT NULL,
                visibility_km REAL NOT NULL,
                cloudiness_percent INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date, location_id)
            )
        """)
        
        # Index för bättre prestanda
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_records (date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_records (location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_date_location ON weather_records (date, location_id)")
        
        self.conn.commit()
        print("✅ Databastabeller skapade")
    
    def insert_location(self, location: Location) -> int:
        """Infoga en plats och returnera ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO locations (name, latitude, longitude)
            VALUES (?, ?, ?)
        """, (location.name, location.latitude, location.longitude))
        
        # Hämta ID för platsen
        cursor.execute("SELECT id FROM locations WHERE name = ?", (location.name,))
        result = cursor.fetchone()
        self.conn.commit()
        return result['id'] if result else None
    
    def insert_weather_record(self, record: WeatherRecord) -> int:
        """Infoga en väderdata-post och returnera ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO weather_records 
            (date, location_id, temperature_c, humidity_percent, wind_speed_ms, 
             wind_direction_degrees, precipitation_mm, pressure_hpa, visibility_km, cloudiness_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.date, record.location_id, record.temperature_c, record.humidity_percent,
            record.wind_speed_ms, record.wind_direction_degrees, record.precipitation_mm,
            record.pressure_hpa, record.visibility_km, record.cloudiness_percent
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_locations(self) -> List[Location]:
        """Hämta alla platser"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM locations ORDER BY name")
        rows = cursor.fetchall()
        
        return [Location(
            id=row['id'],
            name=row['name'],
            latitude=row['latitude'],
            longitude=row['longitude']
        ) for row in rows]
    
    def get_weather_records(self, limit: int = 100, offset: int = 0) -> List[WeatherRecordWithLocation]:
        """Hämta väderdata med platsinformation"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT wr.*, l.name as location_name, l.latitude, l.longitude
            FROM weather_records wr
            JOIN locations l ON wr.location_id = l.id
            ORDER BY wr.date DESC, l.name
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        
        return [WeatherRecordWithLocation(
            id=row['id'],
            date=row['date'],
            location_id=row['location_id'],
            temperature_c=row['temperature_c'],
            humidity_percent=row['humidity_percent'],
            wind_speed_ms=row['wind_speed_ms'],
            wind_direction_degrees=row['wind_direction_degrees'],
            precipitation_mm=row['precipitation_mm'],
            pressure_hpa=row['pressure_hpa'],
            visibility_km=row['visibility_km'],
            cloudiness_percent=row['cloudiness_percent'],
            location=Location(
                id=row['location_id'],
                name=row['location_name'],
                latitude=row['latitude'],
                longitude=row['longitude']
            )
        ) for row in rows]
    
    def get_weather_by_location(self, location_name: str, limit: int = 100) -> List[WeatherRecordWithLocation]:
        """Hämta väderdata för en specifik plats"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT wr.*, l.name as location_name, l.latitude, l.longitude
            FROM weather_records wr
            JOIN locations l ON wr.location_id = l.id
            WHERE l.name LIKE ?
            ORDER BY wr.date DESC
            LIMIT ?
        """, (f"%{location_name}%", limit))
        
        rows = cursor.fetchall()
        
        return [WeatherRecordWithLocation(
            id=row['id'],
            date=row['date'],
            location_id=row['location_id'],
            temperature_c=row['temperature_c'],
            humidity_percent=row['humidity_percent'],
            wind_speed_ms=row['wind_speed_ms'],
            wind_direction_degrees=row['wind_direction_degrees'],
            precipitation_mm=row['precipitation_mm'],
            pressure_hpa=row['pressure_hpa'],
            visibility_km=row['visibility_km'],
            cloudiness_percent=row['cloudiness_percent'],
            location=Location(
                id=row['location_id'],
                name=row['location_name'],
                latitude=row['latitude'],
                longitude=row['longitude']
            )
        ) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hämta statistik från databasen"""
        cursor = self.conn.cursor()
        
        # Grundläggande statistik
        cursor.execute("SELECT COUNT(*) as total_records FROM weather_records")
        total_records = cursor.fetchone()['total_records']
        
        cursor.execute("SELECT COUNT(*) as unique_locations FROM locations")
        unique_locations = cursor.fetchone()['unique_locations']
        
        cursor.execute("SELECT MIN(date) as start_date, MAX(date) as end_date FROM weather_records")
        date_range = cursor.fetchone()
        
        # Temperaturstatistik
        cursor.execute("""
            SELECT MIN(temperature_c) as min_temp, MAX(temperature_c) as max_temp, 
                   AVG(temperature_c) as avg_temp FROM weather_records
        """)
        temp_stats = cursor.fetchone()
        
        # Luftfuktighetsstatistik
        cursor.execute("""
            SELECT MIN(humidity_percent) as min_humidity, MAX(humidity_percent) as max_humidity, 
                   AVG(humidity_percent) as avg_humidity FROM weather_records
        """)
        humidity_stats = cursor.fetchone()
        
        # Nederbördsstatistik
        cursor.execute("""
            SELECT SUM(precipitation_mm) as total_precip, MAX(precipitation_mm) as max_precip, 
                   AVG(precipitation_mm) as avg_precip FROM weather_records
        """)
        precip_stats = cursor.fetchone()
        
        return {
            "total_records": total_records,
            "unique_locations": unique_locations,
            "date_range": {
                "start": date_range['start_date'],
                "end": date_range['end_date']
            },
            "temperature": {
                "min": round(temp_stats['min_temp'], 2),
                "max": round(temp_stats['max_temp'], 2),
                "avg": round(temp_stats['avg_temp'], 2)
            },
            "humidity": {
                "min": humidity_stats['min_humidity'],
                "max": humidity_stats['max_humidity'],
                "avg": round(humidity_stats['avg_humidity'], 2)
            },
            "precipitation": {
                "total": round(precip_stats['total_precip'], 2),
                "max_daily": round(precip_stats['max_precip'], 2),
                "avg": round(precip_stats['avg_precip'], 2)
            }
        }

def import_data_from_api(api_url: str = "http://localhost:8000", db_path: str = "weather.db"):
    """Importera data från API:et till SQLite-databasen"""
    print("🔄 Importerar data från API:et...")
    
    # Skapa databas
    db = WeatherDatabase(db_path)
    db.connect()
    db.create_tables()
    
    try:
        # Hämta platser från API:et
        print("📍 Hämtar platser...")
        response = requests.get(f"{api_url}/weather/locations")
        response.raise_for_status()
        locations_data = response.json()['locations']
        
        # Infoga platser
        location_ids = {}
        for loc_data in locations_data:
            location = Location(
                name=loc_data['plats'],
                latitude=loc_data['latitud'],
                longitude=loc_data['longitud']
            )
            location_id = db.insert_location(location)
            location_ids[location.name] = location_id
            print(f"  ✅ {location.name} (ID: {location_id})")
        
        # Hämta väderdata från API:et
        print("🌤️  Hämtar väderdata...")
        response = requests.get(f"{api_url}/weather?limit=10000")  # Hämta all data
        response.raise_for_status()
        weather_data = response.json()['data']
        
        # Infoga väderdata
        for i, record_data in enumerate(weather_data):
            if i % 500 == 0:
                print(f"  📊 Bearbetar post {i+1}/{len(weather_data)}")
            
            record = WeatherRecord(
                date=record_data['datum'],
                location_id=location_ids[record_data['plats']],
                temperature_c=record_data['temperatur_c'],
                humidity_percent=record_data['luftfuktighet_procent'],
                wind_speed_ms=record_data['vindhastighet_ms'],
                wind_direction_degrees=record_data['vindriktning_grader'],
                precipitation_mm=record_data['nederbord_mm'],
                pressure_hpa=record_data['lufttryck_hpa'],
                visibility_km=record_data['sikt_km'],
                cloudiness_percent=record_data['molnighet_procent']
            )
            db.insert_weather_record(record)
        
        print(f"✅ Importerat {len(weather_data)} väderdata-poster")
        
        # Visa statistik
        stats = db.get_statistics()
        print("\n📊 Databasstatistik:")
        print(f"  Totalt antal poster: {stats['total_records']}")
        print(f"  Antal platser: {stats['unique_locations']}")
        print(f"  Datumintervall: {stats['date_range']['start']} till {stats['date_range']['end']}")
        print(f"  Temperatur: {stats['temperature']['min']}°C till {stats['temperature']['max']}°C")
        print(f"  Genomsnittlig temperatur: {stats['temperature']['avg']}°C")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Fel vid API-anrop: {e}")
        return False
    except Exception as e:
        print(f"❌ Fel vid import: {e}")
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    import_data_from_api()
