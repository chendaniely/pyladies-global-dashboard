import json
import random

from maplibre import Map, MapContext, MapOptions, render_maplibregl
from maplibre.controls import Marker, NavigationControl
import pandas as pd
import geopandas as gpd
from shiny.express import ui

# Include custom CSS
ui.tags.head(
    ui.tags.style("""
.maplibregl-popup-content {
    color: black !important;
}
.maplibregl-popup-content * {
    color: black !important;
}
""")
)

# Import Font Awesome
ui.head_content(
    ui.HTML("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """)
)

# Donation data
current_amount = 12450
target_amount = 20000
donor_count = 145
amount_remaining = max(0, target_amount - current_amount)
progress_pct = (current_amount / target_amount) * 100
is_over_goal = current_amount >= target_amount

# Cap visual progress at 100% but keep the actual percentage for display
visual_progress = min(progress_pct, 100)
bar_color = (
    "#FFD700" if is_over_goal else "#28a745"
)  # Gold if over goal, green otherwise

# Conference metrics
volunteer_count = 42
speaker_count = 28
country_count = 15
language_count = 8
timezone_count = 6

# fake data for country counts
all_countries = [
    "United States of America",
    "Canada",
    "Mexico",
    "Brazil",
    "Argentina",
    "United Kingdom",
    "France",
    "Germany",
    "Italy",
    "Spain",
    "Russia",
    "China",
    "Japan",
    "India",
    "Australia",
    "South Africa",
    "Egypt",
    "Nigeria",
    "Kenya",
    "Morocco",
]

# Randomly select 10 countries
selected_countries = random.sample(all_countries, 10)

# Generate random frequency counts for each country
country_data = {
    country: random.randint(1, 100) for country in selected_countries
}

print("Selected Countries and Frequencies:")
for country, freq in country_data.items():
    print(f"{country}: {freq}")

# Load world geometries from geopandas
world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

# Filter for selected countries and add frequency data
world["frequency"] = world["name"].map(country_data)
world_filtered = world[world["name"].isin(selected_countries)].copy()

# Create GeoJSON from filtered data
# geojson_data = json.loads(world_filtered.to_json())

# Create GeoJSON from filtered data with only the properties we want
geojson_data = json.loads(
    world_filtered[["name", "frequency", "geometry"]].to_json()
)

# Rename properties to proper display names
for feature in geojson_data["features"]:
    country_name = feature["properties"]["name"]
    frequency_value = country_data.get(country_name, 0)

    # Replace properties with properly capitalized names
    feature["properties"] = {
        "Country": country_name,
        "Speakers": frequency_value,
    }

# begin app -----

# Page setup
ui.page_opts(title="Community Conference Dashboard", fillable=True, id="page")
ui.input_dark_mode()


# Create a layout with three value boxes side by side (above map)
with ui.layout_columns(col_widths=[4, 4, 4]):
    # Value Box 1: Main donation amount with vertical progress bar
    ui.value_box(
        title="Fundraising Progress"
        if not is_over_goal
        else "🎉 Goal Exceeded!",
        value=f"${current_amount:,} of ${target_amount:,}",
        showcase=ui.HTML(f"""
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; padding: 10px;">
                <div style="width: 40px; height: 200%; background-color: #e8e8e8;
                            border-radius: 20px; position: relative; border: 2px solid #ddd;">
                    <div style="position: absolute; bottom: 0; width: 100%;
                                height: {visual_progress}%; background-color: {bar_color};
                                border-radius: 18px; transition: height 0.3s ease;
                                display: flex; align-items: center; justify-content: center;">
                    </div>
                    <div style="position: absolute; top: 50%; left: 50%;
                                transform: translate(-50%, -50%);
                                font-weight: bold; font-size: 0.9em; color: #000;
                                text-shadow: 0 0 3px white, 0 0 3px white;">
                        {progress_pct:.0f}%
                    </div>
                </div>
            </div>
        """),
        theme="success" if not is_over_goal else "warning",
    )

    # Value Box 2: Additional metrics
    ui.value_box(
        title="Remaining to Goal" if not is_over_goal else "Stretch Funding",
        value=f"${amount_remaining:,} to go"
        if not is_over_goal
        else f"${current_amount - target_amount:,} over goal!",
        showcase=ui.HTML(f"""
            <div style="display: flex; flex-direction: column; justify-content: center;
                        height: 100%; padding: 10px; color: white;">
                <div style="margin-bottom: 12px; font-size: 1em;">
                    <div style="font-size: 2em; font-weight: bold;">{donor_count}</div>
                    <div style="font-size: 0.9em; opacity: 0.95;">generous donors</div>
                </div>
            </div>
        """),
        theme="primary",
    )

    # Value Box 3: Volunteers
    ui.value_box(
        title="Active Volunteers",
        value=f"{volunteer_count}",
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-users" style="font-size: 3em; color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="info",
    )

# Placeholder for map (you'll add your actual map here)
with ui.card():
    ui.card_header("Where our speakers are")

    # ui.HTML("""
    #     <div style="height: 400px; background-color: #f0f0f0;
    #                 display: flex; align-items: center; justify-content: center;
    #                 border-radius: 5px; color: #666;">
    #         <p style="font-size: 1.2em;">🗺️ Your map will go here</p>
    #     </div>
    # """)
    @render_maplibregl
    def mapgl():
        # Create the map
        m = Map(
            center=(0, 20),
            zoom=1.5,
            style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        )

        # Add navigation control
        m.add_control(NavigationControl())

        # Add GeoJSON source
        m.add_source("countries", {"type": "geojson", "data": geojson_data})

        # Add fill layer with color based on frequency
        m.add_layer({
            "id": "country-fills",
            "type": "fill",
            "source": "countries",
            "paint": {
                "fill-color": [
                    "interpolate",
                    ["linear"],
                    ["get", "Speakers"],
                    0,
                    "#ffffcc",
                    25,
                    "#ffeda0",
                    50,
                    "#fed976",
                    75,
                    "#feb24c",
                    100,
                    "#f03b20",
                ],
                "fill-opacity": 0.7,
            },
        })

        # Add outline layer
        m.add_layer({
            "id": "country-borders",
            "type": "line",
            "source": "countries",
            "paint": {"line-color": "#ffffff", "line-width": 1},
        })

        # Add popup on hover
        m.add_tooltip("country-fills")
        return m


# Create a layout with four value boxes below the map
with ui.layout_columns(col_widths=[3, 3, 3, 3]):
    # Speakers card
    ui.value_box(
        title="Speakers",
        value=f"{speaker_count}",
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-microphone-lines" style="font-size: 2.5em; color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="success",
    )

    # Countries card
    ui.value_box(
        title="Countries",
        value=f"{country_count}",
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-earth-americas" style="font-size: 2.5em; color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="primary",
    )

    # Languages card
    ui.value_box(
        title="Languages",
        value=f"{language_count}",
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-language" style="font-size: 2.5em; color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="info",
    )

    # Time zones card
    ui.value_box(
        title="Time Zones",
        value=f"{timezone_count}",
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-clock" style="font-size: 2.5em; color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="warning",
    )
