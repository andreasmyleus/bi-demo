#!/usr/bin/env python3
"""
Starta Åland Väderdata API
"""

import uvicorn
import os
import sys

def main():
    """Starta FastAPI-servern"""
    print("🌤️  Startar Åland Väderdata API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Dokumentation: http://localhost:8000/docs")
    print("🔄 Tryck Ctrl+C för att stoppa servern")
    print("-" * 50)
    
    # Kontrollera att CSV-filen finns
    if not os.path.exists('aland_weather_data.csv'):
        print("❌ Fel: aland_weather_data.csv hittades inte!")
        print("   Se till att CSV-filen finns i samma mapp som run.py")
        sys.exit(1)
    
    # Starta servern
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print("❌ Port 8000 är redan upptagen!")
            print("   Stoppa den befintliga servern eller använd en annan port")
            print("   Alternativ: python3 -c \"import uvicorn; uvicorn.run('main:app', port=8001)\"")
        else:
            print(f"❌ Fel vid start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

