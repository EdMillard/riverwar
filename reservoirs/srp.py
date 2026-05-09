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
from pathlib import Path
from reservoirs.reservoir import Reservoir, SRPReservoir
from api import df_utils
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from typing import Dict
import datetime
from datetime import datetime, date
import pytz
import pandas as pd
import colorado.allb as all_b
from reservoirs.bartlett import Bartlett
from reservoirs.roosevelt import Roosevelt
from reservoirs.horseshoe import Horseshoe
from reservoirs.saguaro import Saguaro
from reservoirs.canyon import Canyon
from reservoirs.apache import Apache

_url = "https://streamflow.watershedconnection.com/dwr"

class SRP(SRPReservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):

        headers:List[str] = []
        super().__init__('SRP', headers, upstream=upstream)
        self.catalog_id = 0

        self.df_daily:pd.DataFrame = SRPReservoir.from_srp_csv(self.name)

        self.reservoirs:List[SRPReservoir] = [Bartlett(), Roosevelt(), Horseshoe(), Saguaro(), Apache(), Canyon()]

        if self.df_daily is not None:
            # Usage in your code:
            date_time_str = self.df_daily['Date'].iloc[-1]
            self.date_time = df_utils.to_datetime_safe(date_time_str) # type: ignore[arg-type]
            self.active_capacity_af = self.df_daily[all_b.STORAGE].iloc[-1]
        self.elevation_feet = 0
        self.no_elevation_available = True

        # data = get_reservoir_data()

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet =  0
        self.full_af =  1_255_490  + 1_036_200

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 0
        self.power_head_min_af = 0

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

        self.inflow_actual_af = 0
        self.inflow_parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                             ("Projected", 0, Reservoir.inflow_projected_color)]

        # Outflow
        self.outflow_actual_af = 0
        self.release_af = 0
        self.outflow_actual_af = 0
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        # self.reserved_parts = reserved_parts or []

    def get_elevation(self, year, end_year:int|None =None)->float:
        return 0

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        self.elevation_feet = 0.0
        if self.df_daily is not None:
            self.active_capacity_af = self.df_daily[all_b.STORAGE].iloc[-1]

    def chronos(self):
        if self.df_daily is not None:
            if not Reservoir.is_new_day(self.df_daily):
                print(f"  ✓ SRP Reservoirs up to date for today")
                return

        mt_tz = pytz.timezone("US/Mountain")
        now_mt = datetime.now(mt_tz)

        srp_data = get_reservoir_data()
        total = srp_data.get('Total Reservoir System', None)
        if total is not None:
            storage_af = total.get('current_storage_af', None)
            if storage_af is not None:
                self.active_capacity_af = storage_af
                df_utils.set_value_at_datetime(self.df_daily, now_mt, all_b.STORAGE, self.active_capacity_af)
                available_storage_af = total.get('available_storage_af', None)
                if available_storage_af is not None:
                    self.full_af = storage_af + available_storage_af
                SRPReservoir.to_srp_csv(self.name, self.df_daily)

        for name, values in srp_data.items():
            try:
                print(f"  ✓ {name}: {values['current_storage_af']:,} af @ {values['current_elevation_ft']} ft")
            except Exception as e:
                print(f'Exception on print {e}')
            for reservoir in self.reservoirs:
                if name.startswith(reservoir.name):
                    reservoir.receive_data(reservoir.name, reservoir.df_daily, now_mt, values)
                    break

def get_reservoir_data() -> Dict[str, Dict[str, float | int]]:
    """
    Scrapes the reservoir data from https://streamflow.watershedconnection.com/dwr
    Returns individual reservoirs + Total Reservoir System line.
    """
    global _url

    response = requests.get(_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        raise ValueError("Could not find the reservoir table on the page.")

    target_reservoirs = {
        "Roosevelt Lake (Roosevelt Dam)",
        "Apache Lake (Horse Mesa Dam)",
        "Canyon Lake (Mormon Flat Dam)",
        "Saguaro Lake (Stewart Mountain Dam)",
        "Horseshoe Lake (Horseshoe Dam)",
        "Bartlett Lake (Bartlett Dam)"
    }

    data: Dict[str, Dict[str, float | int]] = {}

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        name_cell = cells[0]
        link = name_cell.find("a")
        name = link.get_text(strip=True) if link else name_cell.get_text(strip=True)

        try:
            percent_full = float(cells[1].get_text(strip=True).replace(",", ""))
            current_storage = int(cells[3].get_text(strip=True).replace(",", "")) if cells[3].get_text(strip=True) else None
            available_storage = int(cells[5].get_text(strip=True).replace(",", "")) if cells[5].get_text(strip=True) else None

            # Individual reservoirs
            if name in target_reservoirs:
                current_elevation = float(cells[2].get_text(strip=True).replace(",", ""))
                remaining_elevation = float(cells[4].get_text(strip=True).replace(",", ""))

                data[name] = {
                    "current_elevation_ft": current_elevation,
                    "current_storage_af": current_storage,
                    "remaining_elevation_ft": remaining_elevation,
                    "available_storage_af": available_storage,
                }

            # Total Reservoir System
            elif "Total Reservoir System" in name:
                data["Total Reservoir System"] = {
                    "percent_full": percent_full,
                    "current_storage_af": current_storage,
                    "available_storage_af": available_storage,
                }

        except (ValueError, IndexError, AttributeError):
            continue

    if len(data) < 7:   # 6 reservoirs + total
        print(f"Warning: Only found data for {len(data)} entries (expected 7).")

    return data

if __name__ == "__main__":
    reservoir_info = get_reservoir_data()

    for name in sorted(reservoir_info.keys()):
        v = reservoir_info[name]
        print(f"\n{name}")
        print(f"  Current Elevation : {v['current_elevation_ft']} ft")
        print(f"  Current Storage   : {v['current_storage_af']:,} acre-feet")
        print(f"  Remaining Elevation: {v['remaining_elevation_ft']} ft")
        print(f"  Available Storage : {v['available_storage_af']:,} acre-feet")