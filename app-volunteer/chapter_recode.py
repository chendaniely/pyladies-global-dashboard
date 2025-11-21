import requests
import time
import pandas as pd
from dotenv import load_dotenv
import os
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("GEOCODE_API_KEY")


# Function to geocode a city
def geocode_city(city, api_key):
    url = "https://geocode.maps.co/search"
    params = {"q": city, "api_key": api_key}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]  # Take first result
                return {
                    "latitude": float(result["lat"]),
                    "longitude": float(result["lon"]),
                    "country": result.get("display_name", "").split(", ")[-1],
                }
    except Exception as e:
        print(f"Error geocoding {city}: {e}")

    return None


# Standardize country names to English
def standardize_country(country):
    """Convert country names to standardized English names"""
    country_mapping = {
        # European countries
        "Nederland": "Netherlands",
        "Deutschland": "Germany",
        "Éire / Ireland": "Ireland",
        "España": "Spain",
        "Suomi / Finland": "Finland",
        # Asian countries
        "ประเทศไทย": "Thailand",
        "臺灣": "Taiwan",
        # South American countries
        "Brasil": "Brazil",
        # Already in English
        "United States": "United States",
        "Nigeria": "Nigeria",
        "Colombia": "Colombia",
        "India": "India",
        "Bolivia": "Bolivia",
        "Ghana": "Ghana",
        "Uganda": "Uganda",
        "Malaysia": "Malaysia",
        "Philippines": "Philippines",
        "Moçambique": "Mozambique",
        "Kenya": "Kenya",
        "Canada": "Canada",
        "Namibia": "Namibia",
        "Indonesia": "Indonesia",
    }

    return country_mapping.get(country, country)


# Function to map countries to continents
def get_continent(country):
    continent_map = {
        # Africa
        "Nigeria": "Africa",
        "Namibia": "Africa",
        "Mozambique": "Africa",
        "Kenya": "Africa",
        "Uganda": "Africa",
        "Ghana": "Africa",
        "South Africa": "Africa",
        "Egypt": "Africa",
        "Morocco": "Africa",
        # Asia
        "Thailand": "Asia",
        "India": "Asia",
        "Philippines": "Asia",
        "Indonesia": "Asia",
        "Malaysia": "Asia",
        "Taiwan": "Asia",
        "Singapore": "Asia",
        "Japan": "Asia",
        "South Korea": "Asia",
        "China": "Asia",
        "Vietnam": "Asia",
        # Europe
        "Netherlands": "Europe",
        "Germany": "Europe",
        "Ireland": "Europe",
        "Finland": "Europe",
        "United Kingdom": "Europe",
        "France": "Europe",
        "Spain": "Europe",
        "Italy": "Europe",
        "Portugal": "Europe",
        "Sweden": "Europe",
        "Norway": "Europe",
        "Denmark": "Europe",
        "Poland": "Europe",
        "Czech Republic": "Europe",
        "Austria": "Europe",
        # North America
        "United States": "North America",
        "United States of America": "North America",
        "USA": "North America",
        "Canada": "North America",
        "Mexico": "North America",
        # South America
        "Colombia": "South America",
        "Bolivia": "South America",
        "Brazil": "South America",
        "Argentina": "South America",
        "Chile": "South America",
        "Peru": "South America",
        # Oceania
        "Australia": "Oceania",
        "New Zealand": "Oceania",
    }

    # Check for partial matches
    for key, value in continent_map.items():
        if key.lower() in country.lower():
            return value

    return "Unknown"


# Geocode each chapter
geocoded_data = []

url = "https://portal.pyladies.com/stats.json"
response = requests.get(url)
data = response.json()
stats = data["stats"]

# dictionary of DataFrames keyed by chart_id
breakdown_dfs = {}
for item in stats["volunteer_breakdown"]:
    breakdown_dfs[item["chart_id"]] = pd.DataFrame(
        item["data"], columns=item["columns"]
    )

df_by_chapter = (
    breakdown_dfs["volunteer_by_chapter"]
    .sort_values("Chapter")
    .reset_index(drop=True)
)
df_by_region = (
    breakdown_dfs["volunteers_by_region"]
    .sort_values("Volunteers")
    .reset_index(drop=True)
)
# Geocode each chapter - API calls only -----
geocoded_data = []

for idx, row in tqdm(df_by_chapter.iterrows(), total=len(df_by_chapter)):
    chapter = row["Chapter"]
    volunteers = row["Volunteers"]

    # Geocode the city
    geo_result = geocode_city(chapter, API_KEY)

    if geo_result:
        geocoded_data.append({
            "chapter": chapter,
            "volunteers": volunteers,
            "country_geo": geo_result["country"],
            "latitude": geo_result["latitude"],
            "longitude": geo_result["longitude"],
        })
    else:
        geocoded_data.append({
            "chapter": chapter,
            "volunteers": volunteers,
            "country_geo": "Not found",
            "latitude": None,
            "longitude": None,
        })

    # Rate limit: 5 requests per second
    time.sleep(0.21)

# Create dataframe with geocoded data
df_geocoded = pd.DataFrame(geocoded_data)

# Standardize country names -----

df_geocoded["country"] = df_geocoded["country_geo"].apply(standardize_country)

# Add continent column based on country -----

df_geocoded["continent"] = df_geocoded["country"].apply(get_continent)

# Check results
df_geocoded

# Save to CSV
df_geocoded.to_csv("app-volunteer/chapter_geocoded.csv", index=False)
