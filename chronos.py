import time
import datetime
import schedule
import pytz
from typing import Optional
# Scrapers
from reservoirs.srp import SRP
from reservoirs import lake_pleasant

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
    now_mt = datetime.datetime.now(mt_tz)
    print(f"\n=== Chronos scrape Started: {now_mt.strftime('%Y-%m-%d %I:%M %p')} MT ===")

    try:
        # === AZ Salt River Project(SRP) Reservoir Scraper ===
        #
        print("Fetching reservoir data...")
        _srp.chronos()
    except Exception as e:
        print(f"❌ Error during SRP daily task: {e}")

    # === AZ Lake Pleasant(CAP) Reservoir Scraper ===
    #
    try:
        if _lake_pleasant is None:
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

    except Exception as e:
        print(f"❌ Error during daily tasks: {e}")

def chronos():
    mt_tz = pytz.timezone("US/Mountain")

    schedule_time = "07:00"  # 7:00 AM Mountain Time (auto handles MST/MDT)

    print("Daily Scheduler Started (Colorado Mountain Time)")
    print(f"Tasks scheduled daily at {schedule_time} MT")
    print(f"Current time: {datetime.datetime.now(mt_tz).strftime('%Y-%m-%d %I:%M %p %Z')}\n")

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