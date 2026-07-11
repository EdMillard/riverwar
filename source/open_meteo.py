"""
Copyright (c) 2026 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

def get_historical_weather(lat, lon, start_date="1980-01-01", end_date="2025-12-31"):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        # "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum",
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,snowfall_sum,et0_fao_evapotranspiration,shortwave_radiation_sum,wind_speed_10m_max",
        "timezone": "America/Denver",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()['daily']
        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['time'])
        return df
    else:
        print("Error:", response.text)
        return None

def save_dataframe_to_csv(df: pd.DataFrame,
                          filename: str = None,
                          output_dir: str = ".",
                          index: bool = True,
                          timestamp: bool = True) -> str:
    """
    Save DataFrame to CSV with sensible defaults.
    """
    if filename is None:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_export_{timestamp_str}.csv"

    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=index)

    print(f"✅ Saved {len(df):,} rows to: {output_path}")
    return str(output_path)

def get_location_info(lat, lon):
    url = "https://api.open-meteo.com/v1/elevation"
    params = {
        "latitude": lat,
        "longitude": lon
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        elev_m = data['elevation'][0]          # Take first (only) value
        elev_ft = elev_m * 3.28084
        print(f"Elevation: {elev_m:.1f} meters ({elev_ft:.1f} feet)")
        return elev_m
    else:
        print("Error:", response.text)
        return None

if __name__ == "__main__":
    # This is gridded, i.e. PRISM going back to 1940, convenient but not very trustworthy
    # name = "rico"
    # lat = 37.7
    # lon = -108.0

    # Lizard head SNOTEL
    name = "lizard_head"
    lat = 37.799991
    lon = -107.933968

    #
    # El Diente SNOTEL
    # name = "el_diente"
    # lat = 37.79
    # lon = -108.02

    get_location_info(lat, lon)

    start_date = "1940-01-01"
    end_date = "2026-07-10"

    df = get_historical_weather(lat, lon,  start_date=start_date, end_date=end_date)
    if df is not None:
        open_meteo_file_dir: str = "/opt/dev/riverwar/data/OpenMeteo/"
        output_path = Path(f"{open_meteo_file_dir}/")
        output_path = output_path / f"{name}_{lat}_{lon}_{start_date}_{end_date}_daily.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_dataframe_to_csv(df, str(output_path))
        print(output_path)