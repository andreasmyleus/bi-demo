# 🌤️ Åland Väderdata API

En FastAPI-applikation som tillhandahåller väderdata från olika platser på Åland i JSON-format.

## 🚀 Snabbstart

### 1. Installera beroenden
```bash
pip install -r requirements.txt
```

### 2. Starta servern
```bash
python3 run.py
```

### 3. Öppna i webbläsaren
- **API**: http://localhost:8000
- **Dokumentation**: http://localhost:8000/docs

## 📊 Data

- **1000 rader** väderdata
- **10 platser** på Åland
- **100 dagar** (1 januari - 9 april 2024)
- **12 mätvärden** per post

### Platser
- Mariehamn, Jomala, Finström, Sund, Hammarland
- Saltvik, Geta, Eckerö, Lemland, Lumparland

## 🔗 API Endpoints

### Huvudendpoints
- `GET /` - API-information
- `GET /weather` - Väderdata med filter
- `GET /weather/locations` - Lista över platser
- `GET /weather/dates` - Lista över datum
- `GET /weather/stats` - Statistik
- `GET /weather/location/{name}` - Data för specifik plats

### Filtreringsmöjligheter
- `location` - Filtrera på plats
- `date` - Specifikt datum (YYYY-MM-DD)
- `start_date` / `end_date` - Datumintervall
- `limit` - Max antal rader

## 📝 Exempel

### Hämta alla platser
```bash
curl "http://localhost:8000/weather/locations"
```

### Hämta data för Mariehamn
```bash
curl "http://localhost:8000/weather?location=Mariehamn&limit=5"
```

### Hämta statistik
```bash
curl "http://localhost:8000/weather/stats"
```

### Filtrera på datumintervall
```bash
curl "http://localhost:8000/weather?start_date=2024-01-01&end_date=2024-01-07"
```

## 📋 Dataformat

Varje väderdata-post innehåller:
- `datum` - Datum (YYYY-MM-DD)
- `plats` - Platsnamn
- `latitud` / `longitud` - Koordinater
- `temperatur_c` - Temperatur i Celsius
- `luftfuktighet_procent` - Luftfuktighet i procent
- `vindhastighet_ms` - Vindhastighet i m/s
- `vindriktning_grader` - Vindriktning i grader
- `nederbord_mm` - Nederbörd i millimeter
- `lufttryck_hpa` - Lufttryck i hektopascal
- `sikt_km` - Sikt i kilometer
- `molnighet_procent` - Molnighet i procent

## 🛠️ Utveckling

### Starta i utvecklingsläge
```bash
python3 run.py
```

### Alternativ start
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Filer

- `main.py` - FastAPI-applikation
- `run.py` - Startskript
- `aland_weather_data.csv` - Väderdata
- `requirements.txt` - Python-beroenden
- `README.md` - Denna fil

