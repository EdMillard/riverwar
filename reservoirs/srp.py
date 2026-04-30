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
from datetime import date
from reservoirs.reservoir import Reservoir, SRPReservoir
from source import usbr_rise
import colorado.lb as lb
from api import df_utils
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from typing import Dict
import datetime
import pytz
from reservoirs.bartlett import Bartlett
from reservoirs.roosevelt import Roosevelt
from reservoirs.horseshoe import Horseshoe
from reservoirs.saguaro import Saguaro
from reservoirs.canyon import Canyon
from reservoirs.apache import Apache

class SRP(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('SRP', headers, upstream=upstream)
        self.catalog_id = 0

        self.reservoirs:List[SRPReservoir] = [Bartlett(), Roosevelt(), Horseshoe(), Saguaro(), Apache(), Canyon()]
        # data = get_reservoir_data()

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet =  0
        self.full_af = 0

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
        self.outflow_actual_af = self.get_value_by_year(self.water_year, lb.MOHAVE_RELEASE)
        self.release_af = 0
        self.outflow_actual_af = 0
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        # self.reserved_parts = reserved_parts or []

    def load_data(self, report_path:Path, start_date:date, current_date:date, end_date:date):
        self.load_date(None, start_date, current_date, end_date)

    def get_elevation(self, year, end_year:int|None =None)->float:
        usbr_lake_mohave_elevation_ft = 6133
        info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft, water_year_info=self.water_year_info,
                                                  alias=lb.MOHAVE_ELEVATION)
        df_utils.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date', value_column_name=lb.MOHAVE_ELEVATION)
        return daily_elevation_ft[-1]

    def chronos(self):
        mt_tz = pytz.timezone("US/Mountain")
        now_mt = datetime.datetime.now(mt_tz)

        srp_data = get_reservoir_data()
        for name, values in srp_data.items():
            print(f"  ✓ {name}: {values['current_storage_af']:,} af @ {values['current_elevation_ft']} ft")
            for reservoir in self.reservoirs:
                if name.startswith(reservoir.name):
                    reservoir.receive_data(reservoir.name, reservoir.df_daily, now_mt, values)
                    break

def get_reservoir_data() -> Dict[str, Dict[str, float | int]]:
    """
    Scrapes the reservoir data from https://streamflow.watershedconnection.com/dwr
    using the actual HTML table structure.
    """
    url = "https://streamflow.watershedconnection.com/dwr"

    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the main reservoir table
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

        # Reservoir name is in the first cell (inside <a> tag)
        name_cell = cells[0]
        link = name_cell.find("a")
        if link:
            name = link.get_text(strip=True)
        else:
            name = name_cell.get_text(strip=True)

        if name not in target_reservoirs:
            continue

        try:
            # cells:
            # 0: name
            # 1: % full
            # 2: Current Elevation
            # 3: Current Storage
            # 4: Remaining Elevation
            # 5: Available Storage
            current_elevation = float(cells[2].get_text(strip=True).replace(",", ""))
            current_storage = int(cells[3].get_text(strip=True).replace(",", ""))
            remaining_elevation = float(cells[4].get_text(strip=True).replace(",", ""))
            available_storage = int(cells[5].get_text(strip=True).replace(",", ""))

            data[name] = {
                "current_elevation_ft": current_elevation,
                "current_storage_af": current_storage,
                "remaining_elevation_ft": remaining_elevation,
                "available_storage_af": available_storage,
            }
        except (ValueError, IndexError, AttributeError):
            continue  # skip if any parsing fails

    if len(data) < 6:
        print(f"Warning: Only found data for {len(data)} reservoirs.")

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