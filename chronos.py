"""
Copyright (c) 2025 Ed Millard

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
import time
import datetime
import schedule
import pytz
from typing import Optional
# Scrapers
from reservoirs.srp import SRP
from reservoirs import lake_pleasant
import requests
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

import matplotlib
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

_lake_pleasant:Optional[lake_pleasant.LakePleasant] = None
_srp:SRP = SRP()

def run_daily_tasks():
    global _lake_pleasant

    """Run all your daily scrapers."""
    mt_tz = pytz.timezone("US/Mountain")
    now_mt = datetime.now(mt_tz)
    print(f"\n=== Chronos scrape Started: {now_mt.strftime('%Y-%m-%d %I:%M %p')} MT ===")

    try:
        print("Fetching Denver Water reservoir data...")
        download_denverwater_reservoirs()
    except Exception as e:
        print(f"❌ Error during Denver Water daily task: {e}")

    try:
        print("Fetching USBR Lower Colorado hourly data...")
        download_usbr_hourlyweb('data/usbr_lower_colorado_hourly')
    except Exception as e:
        print(f"❌ Error during USBR Lower Colorado hourly data task: {e}")

    try:
        # === AZ Salt River Project(SRP) Reservoir Scraper ===
        #
        print("Fetching SRP reservoir data...")
        _srp.chronos()
    except Exception as e:
        print(f"❌ Error during SRP daily task: {e}")

    # === AZ Lake Pleasant(CAP) Reservoir Scraper ===
    #
    try:
        if _lake_pleasant is None:
            print("Fetching Lake Pleasant reservoir data...")
            _lake_pleasant = lake_pleasant.LakePleasant()
        ok, lake_pleasant_data = _lake_pleasant.get_lake_pleasant_data()
        if ok:
            if lake_pleasant_data is not None:
                print(lake_pleasant_data)
        else:
            print(f"❌ Error during Lake Pleasant daily tasks, schedule retry")
    except Exception as e:
        print(f"❌ Error during Lake Pleasant daily tasks: {e}")

        print("✅ All daily tasks completed successfully.")


def download_usbr_hourlyweb(save_dir: str = ".") -> str:
    """
    Download the USBR Lower Colorado hourlyweb.json file and save it
    with a suffix based on the 'QueryDate' field inside the JSON.

    Example saved filename: hourlyweb_2026-05-20_191016.json

    Returns the full path to the saved file.
    """
    url = "https://www.usbr.gov/lc/region/g4000/riverops/webreports/hourlyweb.json"

    # Download the JSON
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Extract QueryDate (e.g., "5/20/2026 7:10:16 PM")
    query_date_str = data.get("QueryDate")
    if not query_date_str:
        raise ValueError("QueryDate not found in the JSON response")

    # Parse the date string
    dt = datetime.strptime(query_date_str, "%m/%d/%Y %I:%M:%S %p")

    # Create filename suffix: YYYY-MM-DD_HHMMSS
    suffix = dt.strftime("%Y-%m-%d_%H%M%S")

    # Build filename
    filename = f"hourlyweb_{suffix}.json"
    save_path = Path(save_dir) / filename

    # Save the file
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved: {save_path}")
    return str(save_path)

def download_denverwater_reservoirs():
    url = "https://www.denverwater.org/your-water/water-supply-and-planning/reservoir-levels/csv?page&_format=csv"

    # Download the CSV
    response = requests.get(url)
    response.raise_for_status()

    # Read the CSV (skip the separator line)
    df = pd.read_csv(url, skiprows=[1])

    # Get the latest date from the file
    if 'Valid Date' in df.columns:
        df['Valid Date'] = pd.to_datetime(df['Valid Date'], errors='coerce')
        latest_date = df['Valid Date'].max()
        date_str = latest_date.strftime('%Y-%m-%d')
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # Define the target path
    directory = "data/DenverWater"
    filename = f"denverwater_reservoirs_{date_str}.csv"
    full_path = os.path.join(directory, filename)

    # Make sure directory exists
    os.makedirs(directory, exist_ok=True)

    # Save the file
    df.to_csv(full_path, index=False)

    print(f"✅ Successfully saved: {full_path}")

    return full_path


def chronos():
    mt_tz = pytz.timezone("US/Mountain")

    schedule_time = "07:00"  # 7:00 AM Mountain Time (auto handles MST/MDT)

    print("Daily Scheduler Started (Colorado Mountain Time)")
    print(f"Tasks scheduled daily at {schedule_time} MT")
    print(f"Current time: {datetime.now(mt_tz).strftime('%Y-%m-%d %I:%M %p %Z')}\n")

    # Schedule the job - pytz automatically adjusts for DST
    schedule.every().day.at(schedule_time).do(run_daily_tasks)

    # Optional: Run immediately when the script starts (great for testing)
    run_daily_tasks()

    # Keep script alive
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    chronos()