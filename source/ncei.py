"""
Copyright (c) 2022 Ed Millard

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
#
# https://www.ncei.noaa.gov/access/search/dataset-search/?text=&p=1&esriMagicKey=dHA9NCN0dj01OGE2NGNlZSNubT1SaWNvLCBDTywgVVNBI2xuZz00MSNsbj1Xb3JsZA==&downloadable=true
# https://www.ncei.noaa.gov/support/access-search-service-api-user-documentation
#
def search_noaa_stations(keyword="Rico CO", limit=10):
    url = "https://www.ncei.noaa.gov/access/services/search/v1/data"
    params = {
        "dataset": "daily-summaries",   # or "ghcnd"
        "keywords": keyword,
        "limit": limit
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.text)
        return None



def get_noaa_daily_data(station_id, start_date, end_date, token=None):
    """Fetch daily data from NCEI API for a GHCN/COOP station."""
    base_url = "https://www.ncei.noaa.gov/access/services/data/v1"

    params = {
        "dataset": "daily-summaries",
        "stations": station_id,  # e.g., "USC00056789" for Rico area
        "startDate": start_date,  # "1980-01-01"
        "endDate": end_date,  # "2025-12-31"
        "dataTypes": "TMAX,TMIN,TAVG,PRCP",  # Max/min/avg temp, precip
        "format": "json"
    }

    headers = {"token": token} if token else {}

    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values('DATE')
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

if __name__ == "__main__":
    # Example
    results = search_noaa_stations("Rico", 20)
    for station in results.get("results", []):
        print(station["id"], station["name"], station["latitude"], station["longitude"])
    df_rico = get_noaa_daily_data("USC00056789", "1960-01-01", "2025-12-31")
