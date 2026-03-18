
from flask import Flask, render_template, jsonify, request
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import requests
import os


load_dotenv("/storage/emulated/0/AEROSENSE/.env")

app = Flask(__name__)

API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BASE_URL = "http://api.openweathermap.org"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/air-quality")
def air_quality():
    city = request.args.get("city", "London")

    # Get coordinates from city name
    geo_url = f"{BASE_URL}/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    geo_res = requests.get(geo_url).json()

    if not geo_res:
        return jsonify({"error": "City not found"}), 404

    lat = geo_res[0]["lat"]
    lon = geo_res[0]["lon"]
    country = geo_res[0].get("country", "")

    # Get air quality data
    aqi_url = f"{BASE_URL}/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    aqi_res = requests.get(aqi_url).json()

    # Get weather data
    weather_url = f"{BASE_URL}/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    weather_res = requests.get(weather_url).json()

    components = aqi_res["list"][0]["components"]
    aqi = aqi_res["list"][0]["main"]["aqi"]

    aqi_labels = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }

    health_tips = {
        1: "Air quality is great! Perfect for outdoor activities.",
        2: "Air quality is fair. Sensitive individuals should limit prolonged outdoor exertion.",
        3: "Moderate air quality. Consider reducing intense outdoor activities.",
        4: "Poor air quality. Avoid prolonged outdoor exposure. Wear a mask.",
        5: "Very Poor! Stay indoors. Keep windows closed. Use air purifier if available."
    }

    return jsonify({
        "city": city,
        "country": country,
        "lat": lat,
        "lon": lon,
        "aqi": aqi,
        "aqi_label": aqi_labels[aqi],
        "health_tip": health_tips[aqi],
        "components": {
            "pm2_5": round(components["pm2_5"], 2),
            "pm10": round(components["pm10"], 2),
            "co": round(components["co"], 2),
            "no2": round(components["no2"], 2),
            "o3": round(components["o3"], 2),
            "so2": round(components["so2"], 2),
        },
        "weather": {
            "temp": weather_res["main"]["temp"],
            "humidity": weather_res["main"]["humidity"],
            "description": weather_res["weather"][0]["description"]
        }
    })

@app.route("/api/top-polluted")
def top_polluted():
    cities = [
        "Delhi", "Lahore", "Dhaka", "Ulaanbaatar", "Bishkek",
        "Baghdad", "Kabul", "Kathmandu", "Cairo", "Jakarta"
    ]

    def fetch_city(city):
        try:
            geo_url = f"{BASE_URL}/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
            geo_res = requests.get(geo_url, timeout=5).json()
            if not geo_res:
                return None
            lat = geo_res[0]["lat"]
            lon = geo_res[0]["lon"]

            aqi_url = f"{BASE_URL}/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
            aqi_res = requests.get(aqi_url, timeout=5).json()
            aqi = aqi_res["list"][0]["main"]["aqi"]
            pm2_5 = aqi_res["list"][0]["components"]["pm2_5"]

            return {
                "city": city,
                "aqi": aqi,
                "pm2_5": round(pm2_5, 2)
            }
        except:
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_city, cities))

    results = [r for r in results if r is not None]
    results.sort(key=lambda x: x["aqi"], reverse=True)
    return jsonify(results[:10])

if __name__ == "__main__":
    app.run(debug=True)
