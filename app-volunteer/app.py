import json

import altair as alt
import geopandas as gpd
import pandas as pd
import requests
from maplibre import render_maplibregl
from maplibre.controls import NavigationControl
from maplibre.map import Map
from shiny.express import render, ui
from shinywidgets import render_altair

# Download the JSON data
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

# Access individual DataFrames
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
df_by_language = (
    breakdown_dfs["volunteers_by_languages"]
    .sort_values("Language")
    .reset_index(drop=True)
)

df = pd.read_csv("app-volunteer/chapter_geocoded.csv")[
    [
        "chapter",
        "latitude",
        "longitude",
        "country",
        "continent",
    ]
]

df_by_chapter_geocode = df_by_chapter.merge(
    df,
    left_on="Chapter",
    right_on="chapter",
    how="left",
).drop(columns=["chapter"])

# Include custom CSS
ui.tags.head(
    ui.tags.style("""`
.maplibregl-popup-content {
    color: black !important;
}
.maplibregl-popup-content * {
    color: black !important;
}
""")
)

# world data -----

# Load world geometries from geopandas
# world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
world = gpd.read_file(
    "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
)
world = world[["CONTINENT", "geometry"]].rename(
    columns={"CONTINENT": "continent"}
)

# Create a mapping of continent names from df_by_region to world dataset
continent_mapping = {
    "Africa": "Africa",
    "Asia": "Asia",
    "Europe": "Europe",
    "North America": "North America",
    "South America": "South America",
    "Oceania": "Oceania",
}

# Create a dictionary of volunteer counts by continent
continent_volunteers = df_by_region.set_index("Region")["Volunteers"].to_dict()

# Add volunteer counts to world data based on continent
world["Volunteers"] = world["continent"].map(continent_volunteers)

# Filter to only continents that have data
world_filtered = world[
    world["continent"].isin(df_by_region["Region"].tolist())
].copy()

# Create GeoJSON from filtered data
geojson_data = json.loads(
    world_filtered[["continent", "Volunteers", "geometry"]].to_json()
)

# Rename properties to proper display names
for feature in geojson_data["features"]:
    continent_name = feature["properties"]["continent"]
    volunteer_count = feature["properties"]["Volunteers"]

    feature["properties"] = {
        "Continent": continent_name,
        "Volunteers": volunteer_count,
    }

# begin app -----

# Page setup
ui.page_opts(title="Community Conference Dashboard", fillable=True, id="page")

# Placeholder for map (you'll add your actual map here)
with ui.card():
    ui.card_header("Total Volunteers by Continent")

    @render_maplibregl
    def mapgl():
        # Create the map
        m = Map(
            center=(0, 20),
            zoom=1.5,
            style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        )

        # Add navigation control
        m.add_control(
            NavigationControl(
                show_compass=False,
                show_zoom=True,
                position="top-right",
                visualize_pitch=False,
            )
        )

        # Add GeoJSON source
        m.add_source("continents", {"type": "geojson", "data": geojson_data})

        # Add fill layer with color based on volunteer count
        m.add_layer({
            "id": "continent-fills",
            "type": "fill",
            "source": "continents",
            "paint": {
                "fill-color": [
                    "interpolate",
                    ["linear"],
                    ["get", "Volunteers"],
                    1,
                    "#ffffcc",
                    15,
                    "#ffeda0",
                    25,
                    "#fed976",
                    35,
                    "#feb24c",
                    42,
                    "#f03b20",
                ],
                "fill-opacity": 0.7,
            },
        })

        # Add outline layer
        m.add_layer({
            "id": "continent-borders",
            "type": "line",
            "source": "continents",
            "paint": {"line-color": "#ffffff", "line-width": 1},
        })

        # Add popup on hover
        m.add_tooltip("continent-fills")
        return m


with ui.card():
    ui.card_header("Our Chapter Volunteers")

    @render_maplibregl
    def chapter_map():
        # Create GeoJSON from the geocoded chapter data
        chapters_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "Chapter": row["Chapter"],
                        "Volunteers": row["Volunteers"],
                        "Country": row["country"],
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row["longitude"], row["latitude"]],
                    },
                }
                for _, row in df_by_chapter_geocode.iterrows()
                if pd.notna(row["latitude"]) and pd.notna(row["longitude"])
            ],
        }

        # Create the map
        m = Map(
            center=(20, 10),
            zoom=1.5,
            style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        )

        # Add navigation control
        m.add_control(
            NavigationControl(
                show_compass=False,
                show_zoom=True,
                position="top-right",
                visualize_pitch=False,
            )
        )

        # Add GeoJSON source for chapters
        m.add_source("chapters", {"type": "geojson", "data": chapters_geojson})

        # Add circle layer with size and color based on volunteer count
        m.add_layer({
            "id": "chapter-circles",
            "type": "circle",
            "source": "chapters",
            "paint": {
                "circle-radius": [
                    "interpolate",
                    ["linear"],
                    ["get", "Volunteers"],
                    1,
                    6,
                    3,
                    10,
                    6,
                    15,
                    9,
                    20,
                ],
                "circle-color": [
                    "interpolate",
                    ["linear"],
                    ["get", "Volunteers"],
                    1,
                    "#fc9272",
                    3,
                    "#fb6a4a",
                    6,
                    "#ef3b2c",
                    9,
                    "#cb181d",
                ],
                "circle-opacity": 0.8,
                "circle-stroke-width": 2,
                "circle-stroke-color": "#ffffff",
            },
        })

        # Add popup on hover
        m.add_tooltip("chapter-circles")

        return m


with ui.card():
    ui.card_header("Languages Spoken by Volunteers")

    @render.text
    def english_language_text():
        english_volunteers = df_by_language.loc[
            df_by_language["Language"] == "English", "Volunteers"
        ].values
        if len(english_volunteers) > 0:
            return f"Number of volunteers who speak English: {english_volunteers[0]}"
        else:
            return "No volunteers speak English."

    @render.text
    def single_language_text():
        single_volunteer_languages = (
            df_by_language.loc[df_by_language["Volunteers"] == 1, "Language"]
            .sort_values()
            .tolist()
        )
        if single_volunteer_languages:
            return "Languages with a single volunteer: " + ", ".join(
                single_volunteer_languages
            )
        else:
            return "All languages have multiple volunteers."

    @render_altair
    def plot_language_alt():
        df_plot = df_by_language.loc[
            (df_by_language["Language"] != "English")
            & (df_by_language["Volunteers"] > 1),
            :,
        ].sort_values("Volunteers", ascending=False)

        return (
            alt.Chart(df_plot)
            .mark_bar()
            .encode(
                x=alt.X("Volunteers:Q", title="Volunteers"),
                y=alt.Y("Language:N", sort="-x", title=None),
                color=alt.Color("Language:N", legend=None),
                tooltip=["Language:N", "Volunteers:Q"],
            )
            .properties(width=600, height=400)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=False, domain=False)
        )
