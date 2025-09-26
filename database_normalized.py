#!/usr/bin/env python3
"""
Normaliserad SQLite-databas för Åland väderdata
Varje väderentitet har sin egen tabell
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from models import Location, WeatherRecord, WeatherRecordWithLocation
import requests
import json

class NormalizedWeatherDatabase:
    """Hanterar normaliserad SQLite-databas för väderdata"""
    
    def __init__(self, db_path: str = "weather_normalized.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Anslut till databasen"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Stäng databasanslutningen"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Skapa normaliserade tabeller"""
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
        
        # Tabell för datum
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                day_of_year INTEGER NOT NULL,
                season TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabell för temperatur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temperatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                temperature_c REAL NOT NULL,
                temperature_f REAL NOT NULL,
                feels_like_c REAL,
                min_temperature_c REAL,
                max_temperature_c REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Tabell för luftfuktighet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS humidity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                humidity_percent INTEGER NOT NULL,
                dew_point_c REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Tabell för vind
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wind (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                wind_speed_ms REAL NOT NULL,
                wind_speed_kmh REAL NOT NULL,
                wind_direction_degrees REAL NOT NULL,
                wind_direction_text TEXT,
                wind_gust_ms REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Tabell för nederbörd
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS precipitation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                precipitation_mm REAL NOT NULL,
                precipitation_inches REAL NOT NULL,
                precipitation_type TEXT,
                snow_depth_cm REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Tabell för lufttryck
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pressure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                pressure_hpa REAL NOT NULL,
                pressure_inhg REAL NOT NULL,
                pressure_trend TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Tabell för sikt
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                visibility_km REAL NOT NULL,
                visibility_miles REAL NOT NULL,
                fog_density TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Tabell för molnighet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cloudiness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                cloudiness_percent INTEGER NOT NULL,
                cloud_type TEXT,
                cloud_height_m REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date_id) REFERENCES dates (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                UNIQUE(date_id, location_id)
            )
        """)
        
        # Index för bättre prestanda
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dates_date ON dates (date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dates_year ON dates (year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dates_season ON dates (season)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temperatures_date_location ON temperatures (date_id, location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_humidity_date_location ON humidity (date_id, location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wind_date_location ON wind (date_id, location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_precipitation_date_location ON precipitation (date_id, location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pressure_date_location ON pressure (date_id, location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visibility_date_location ON visibility (date_id, location_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cloudiness_date_location ON cloudiness (date_id, location_id)")
        
        self.conn.commit()
        print("✅ Normaliserade databastabeller skapade")
    
    def get_season(self, month: int) -> str:
        """Bestäm årstid baserat på månad"""
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"
    
    def insert_date(self, date_obj: date) -> int:
        """Infoga datum och returnera ID"""
        cursor = self.conn.cursor()
        season = self.get_season(date_obj.month)
        day_of_year = date_obj.timetuple().tm_yday
        
        cursor.execute("""
            INSERT OR IGNORE INTO dates (date, year, month, day, day_of_year, season)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_obj, date_obj.year, date_obj.month, date_obj.day, day_of_year, season))
        
        # Hämta ID för datumet
        cursor.execute("SELECT id FROM dates WHERE date = ?", (date_obj,))
        result = cursor.fetchone()
        self.conn.commit()
        return result['id'] if result else None
    
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
    
    def insert_temperature(self, date_id: int, location_id: int, temperature_c: float):
        """Infoga temperaturdata"""
        cursor = self.conn.cursor()
        temperature_f = (temperature_c * 9/5) + 32  # Konvertera till Fahrenheit
        
        cursor.execute("""
            INSERT OR REPLACE INTO temperatures 
            (date_id, location_id, temperature_c, temperature_f, feels_like_c, min_temperature_c, max_temperature_c)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date_id, location_id, temperature_c, temperature_f, temperature_c, temperature_c, temperature_c))
        
        self.conn.commit()
    
    def insert_humidity(self, date_id: int, location_id: int, humidity_percent: int):
        """Infoga luftfuktighetsdata"""
        cursor = self.conn.cursor()
        # Beräkna daggpunkt (ungefärlig formel)
        dew_point_c = humidity_percent * 0.1  # Förenklad beräkning
        
        cursor.execute("""
            INSERT OR REPLACE INTO humidity 
            (date_id, location_id, humidity_percent, dew_point_c)
            VALUES (?, ?, ?, ?)
        """, (date_id, location_id, humidity_percent, dew_point_c))
        
        self.conn.commit()
    
    def insert_wind(self, date_id: int, location_id: int, wind_speed_ms: float, wind_direction_degrees: float):
        """Infoga vinddata"""
        cursor = self.conn.cursor()
        wind_speed_kmh = wind_speed_ms * 3.6  # Konvertera till km/h
        
        # Konvertera vindriktning till text
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        direction_index = int((wind_direction_degrees + 11.25) / 22.5) % 16
        wind_direction_text = directions[direction_index]
        
        cursor.execute("""
            INSERT OR REPLACE INTO wind 
            (date_id, location_id, wind_speed_ms, wind_speed_kmh, wind_direction_degrees, wind_direction_text, wind_gust_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date_id, location_id, wind_speed_ms, wind_speed_kmh, wind_direction_degrees, wind_direction_text, wind_speed_ms * 1.2))
        
        self.conn.commit()
    
    def insert_precipitation(self, date_id: int, location_id: int, precipitation_mm: float):
        """Infoga nederbördsdata"""
        cursor = self.conn.cursor()
        precipitation_inches = precipitation_mm / 25.4  # Konvertera till inches
        
        # Bestäm nederbördstyp baserat på mängd
        if precipitation_mm == 0:
            precipitation_type = "None"
        elif precipitation_mm < 1:
            precipitation_type = "Light"
        elif precipitation_mm < 5:
            precipitation_type = "Moderate"
        else:
            precipitation_type = "Heavy"
        
        cursor.execute("""
            INSERT OR REPLACE INTO precipitation 
            (date_id, location_id, precipitation_mm, precipitation_inches, precipitation_type, snow_depth_cm)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_id, location_id, precipitation_mm, precipitation_inches, precipitation_type, precipitation_mm * 0.1))
        
        self.conn.commit()
    
    def insert_pressure(self, date_id: int, location_id: int, pressure_hpa: float):
        """Infoga lufttrycksdata"""
        cursor = self.conn.cursor()
        pressure_inhg = pressure_hpa * 0.02953  # Konvertera till inches of mercury
        
        cursor.execute("""
            INSERT OR REPLACE INTO pressure 
            (date_id, location_id, pressure_hpa, pressure_inhg, pressure_trend)
            VALUES (?, ?, ?, ?, ?)
        """, (date_id, location_id, pressure_hpa, pressure_inhg, "Stable"))
        
        self.conn.commit()
    
    def insert_visibility(self, date_id: int, location_id: int, visibility_km: float):
        """Infoga siktdata"""
        cursor = self.conn.cursor()
        visibility_miles = visibility_km * 0.621371  # Konvertera till miles
        
        # Bestäm dimma baserat på sikt
        if visibility_km < 1:
            fog_density = "Dense"
        elif visibility_km < 5:
            fog_density = "Moderate"
        elif visibility_km < 10:
            fog_density = "Light"
        else:
            fog_density = "Clear"
        
        cursor.execute("""
            INSERT OR REPLACE INTO visibility 
            (date_id, location_id, visibility_km, visibility_miles, fog_density)
            VALUES (?, ?, ?, ?, ?)
        """, (date_id, location_id, visibility_km, visibility_miles, fog_density))
        
        self.conn.commit()
    
    def insert_cloudiness(self, date_id: int, location_id: int, cloudiness_percent: int):
        """Infoga molnighetsdata"""
        cursor = self.conn.cursor()
        
        # Bestäm molntyp baserat på molnighet
        if cloudiness_percent < 25:
            cloud_type = "Clear"
        elif cloudiness_percent < 50:
            cloud_type = "Partly Cloudy"
        elif cloudiness_percent < 75:
            cloud_type = "Mostly Cloudy"
        else:
            cloud_type = "Overcast"
        
        cursor.execute("""
            INSERT OR REPLACE INTO cloudiness 
            (date_id, location_id, cloudiness_percent, cloud_type, cloud_height_m)
            VALUES (?, ?, ?, ?, ?)
        """, (date_id, location_id, cloudiness_percent, cloud_type, cloudiness_percent * 10))
        
        self.conn.commit()
    
    def get_table_stats(self) -> Dict[str, Any]:
        """Hämta statistik för alla tabeller"""
        cursor = self.conn.cursor()
        
        tables = ['locations', 'dates', 'temperatures', 'humidity', 'wind', 
                 'precipitation', 'pressure', 'visibility', 'cloudiness']
        
        stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            stats[table] = count
        
        return stats

def import_data_to_normalized_db(api_url: str = "http://localhost:8000", db_path: str = "weather_normalized.db"):
    """Importera data till normaliserad databas"""
    print("🔄 Importerar data till normaliserad databas...")
    
    # Skapa databas
    db = NormalizedWeatherDatabase(db_path)
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
        response = requests.get(f"{api_url}/weather?limit=10000")
        response.raise_for_status()
        weather_data = response.json()['data']
        
        # Infoga väderdata
        for i, record_data in enumerate(weather_data):
            if i % 500 == 0:
                print(f"  📊 Bearbetar post {i+1}/{len(weather_data)}")
            
            # Infoga datum
            date_obj = datetime.strptime(record_data['datum'], '%Y-%m-%d').date()
            date_id = db.insert_date(date_obj)
            
            location_id = location_ids[record_data['plats']]
            
            # Infoga varje väderentitet i sin egen tabell
            db.insert_temperature(date_id, location_id, record_data['temperatur_c'])
            db.insert_humidity(date_id, location_id, record_data['luftfuktighet_procent'])
            db.insert_wind(date_id, location_id, record_data['vindhastighet_ms'], record_data['vindriktning_grader'])
            db.insert_precipitation(date_id, location_id, record_data['nederbord_mm'])
            db.insert_pressure(date_id, location_id, record_data['lufttryck_hpa'])
            db.insert_visibility(date_id, location_id, record_data['sikt_km'])
            db.insert_cloudiness(date_id, location_id, record_data['molnighet_procent'])
        
        print(f"✅ Importerat {len(weather_data)} väderdata-poster")
        
        # Visa statistik
        stats = db.get_table_stats()
        print("\n📊 Tabellstatistik:")
        for table, count in stats.items():
            print(f"  {table}: {count} poster")
        
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
    import_data_to_normalized_db()
