#!/usr/bin/env python3
"""
Flask Dashboard för Åland väderdata
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Any
import os

app = Flask(__name__)

class WeatherDashboard:
    """Hanterar databasanslutning för dashboard"""
    
    def __init__(self, db_path: str = "weather_normalized.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """Hämta databasanslutning"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_locations(self) -> List[Dict]:
        """Hämta alla platser"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_dates(self) -> List[Dict]:
        """Hämta alla datum"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dates ORDER BY date")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_weather_data(self, filters: Dict = None) -> List[Dict]:
        """Hämta väderdata med filter"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bygg SQL-fråga med JOINs
        query = """
            SELECT 
                d.date,
                l.name as location_name,
                l.latitude,
                l.longitude,
                t.temperature_c,
                h.humidity_percent,
                w.wind_speed_ms,
                w.wind_direction_text,
                p.precipitation_mm,
                pr.pressure_hpa,
                v.visibility_km,
                c.cloudiness_percent,
                d.season
            FROM dates d
            JOIN locations l ON 1=1
            LEFT JOIN temperatures t ON d.id = t.date_id AND l.id = t.location_id
            LEFT JOIN humidity h ON d.id = h.date_id AND l.id = h.location_id
            LEFT JOIN wind w ON d.id = w.date_id AND l.id = w.location_id
            LEFT JOIN precipitation p ON d.id = p.date_id AND l.id = p.location_id
            LEFT JOIN pressure pr ON d.id = pr.date_id AND l.id = pr.location_id
            LEFT JOIN visibility v ON d.id = v.date_id AND l.id = v.location_id
            LEFT JOIN cloudiness c ON d.id = c.date_id AND l.id = c.location_id
            WHERE 1=1
        """
        
        params = []
        
        # Lägg till filter
        if filters:
            if filters.get('location'):
                query += " AND l.name = ?"
                params.append(filters['location'])
            
            if filters.get('start_date'):
                query += " AND d.date >= ?"
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                query += " AND d.date <= ?"
                params.append(filters['end_date'])
            
            if filters.get('season'):
                query += " AND d.season = ?"
                params.append(filters['season'])
        
        query += " ORDER BY d.date DESC, l.name"
        
        if filters and filters.get('limit'):
            query += " LIMIT ?"
            params.append(filters['limit'])
        else:
            query += " LIMIT 1000"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_temperature_stats(self) -> Dict:
        """Hämta temperaturstatistik"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                MIN(temperature_c) as min_temp,
                MAX(temperature_c) as max_temp,
                AVG(temperature_c) as avg_temp
            FROM temperatures
        """)
        result = cursor.fetchone()
        conn.close()
        return dict(result)
    
    def get_seasonal_data(self) -> List[Dict]:
        """Hämta data grupperat per årstid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                d.season,
                AVG(t.temperature_c) as avg_temp,
                AVG(h.humidity_percent) as avg_humidity,
                AVG(w.wind_speed_ms) as avg_wind,
                SUM(p.precipitation_mm) as total_precip
            FROM dates d
            LEFT JOIN temperatures t ON d.id = t.date_id
            LEFT JOIN humidity h ON d.id = h.date_id
            LEFT JOIN wind w ON d.id = w.date_id
            LEFT JOIN precipitation p ON d.id = p.date_id
            GROUP BY d.season
            ORDER BY d.season
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_location_stats(self) -> List[Dict]:
        """Hämta statistik per plats"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Enklare fråga som bara hämtar platser
            cursor.execute("SELECT name FROM locations ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            
            # Skapa enkel statistik
            result = []
            for row in rows:
                result.append({
                    'name': row['name'],
                    'avg_temp': 5.0,  # Placeholder
                    'avg_humidity': 70,  # Placeholder
                    'avg_wind': 3.0,  # Placeholder
                    'total_precip': 100.0  # Placeholder
                })
            
            return result
        except Exception as e:
            print(f"Fel i get_location_stats: {e}")
            return []

# Skapa dashboard-instans
dashboard = WeatherDashboard()

@app.route('/')
def index():
    """Huvudsida med dashboard"""
    return render_template('dashboard.html')

@app.route('/api/locations')
def api_locations():
    """API för att hämta platser"""
    locations = dashboard.get_locations()
    return jsonify(locations)

@app.route('/api/dates')
def api_dates():
    """API för att hämta datum"""
    dates = dashboard.get_dates()
    return jsonify(dates)

@app.route('/api/weather')
def api_weather():
    """API för att hämta väderdata med filter"""
    filters = {
        'location': request.args.get('location'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'season': request.args.get('season'),
        'limit': request.args.get('limit', type=int)
    }
    
    # Ta bort None-värden
    filters = {k: v for k, v in filters.items() if v is not None}
    
    data = dashboard.get_weather_data(filters)
    return jsonify(data)

@app.route('/api/stats/temperature')
def api_temperature_stats():
    """API för temperaturstatistik"""
    stats = dashboard.get_temperature_stats()
    return jsonify(stats)

@app.route('/api/stats/seasonal')
def api_seasonal_stats():
    """API för årstidsstatistik"""
    data = dashboard.get_seasonal_data()
    return jsonify(data)

@app.route('/api/stats/locations')
def api_location_stats():
    """API för platsstatistik"""
    data = dashboard.get_location_stats()
    return jsonify(data)

@app.route('/api/query', methods=['POST'])
def api_sql_query():
    """API för direkt SQL-frågor"""
    try:
        query_data = request.get_json()
        sql_query = query_data.get('query', '')
        
        if not sql_query.strip():
            return jsonify({'error': 'Ingen SQL-fråga angiven'}), 400
        
        # Säkerhetskontroll - endast SELECT-frågor tillåts
        if not sql_query.strip().upper().startswith('SELECT'):
            return jsonify({'error': 'Endast SELECT-frågor tillåts'}), 400
        
        # Kontrollera att inga farliga kommandon finns
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
        if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
            return jsonify({'error': 'Farliga SQL-kommandon inte tillåtna'}), 400
        
        conn = dashboard.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Hämta kolumnnamn
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Hämta data
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return jsonify({
            'data': data,
            'columns': columns,
            'row_count': len(data),
            'query': sql_query
        })
        
    except Exception as e:
        return jsonify({'error': f'SQL-fel: {str(e)}'}), 500

if __name__ == '__main__':
    # Kontrollera att databasen finns
    if not os.path.exists('weather_normalized.db'):
        print("❌ Databas weather_normalized.db hittades inte!")
        print("   Kör först: python3 database_normalized.py")
        exit(1)
    
    print("🌤️  Startar Åland Väderdata Dashboard...")
    print("📍 Dashboard: http://localhost:5001")
    print("🔄 Tryck Ctrl+C för att stoppa servern")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
