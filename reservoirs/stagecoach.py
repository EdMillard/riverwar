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
# https://www.upperyampawater.gov/stagecoach-reservoir
from pathlib import Path
from datetime import date
from reservoirs.reservoir import Reservoir
from typing import List, Optional
import requests
import re


class Stagecoach(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Stagecoach',headers,  catalog_id=0, upstream=upstream)
        self.start_year = 1989
        self.no_elevation_available = True

        # Elevations
        #
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet = 7_200
        self.full_af = 36_439

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 0
        self.power_head_min_af = 0

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

    @staticmethod
    def get_stagecoach_storage(url="https://www.upperyampawater.gov/stagecoach-reservoir"):
        """
        Fetch current Stagecoach Reservoir storage (acre-feet) from the UYWCD page.

        Returns:
            dict with storage_af, capacity_af, updated, and raw text snippet,
            or None on failure.
        """
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            text = resp.text

            # Extract storage
            storage_match = re.search(r"Current Storage Volume:\s*([\d,]+)\s*AF", text, re.IGNORECASE)
            capacity_match = re.search(r"Total Capacity:\s*([\d,]+)\s*AF", text, re.IGNORECASE)
            updated_match = re.search(r"Updated\s+([0-9/]+)", text, re.IGNORECASE)

            storage_af = int(storage_match.group(1).replace(",", "")) if storage_match else None
            capacity_af = int(capacity_match.group(1).replace(",", "")) if capacity_match else None
            updated = updated_match.group(1) if updated_match else None

            return {
                "storage_af": storage_af,
                "capacity_af": capacity_af,
                "updated": updated,
                "url": url
            }
        except Exception as e:
            print(f"Error fetching Stagecoach storage: {e}")
            return None

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        super().load_data(report_path, start_date, current_date, end_date)

        data = Stagecoach.get_stagecoach_storage()
        if data:
            self.active_capacity_af = data.get('storage_af', 0)
            self.elevation_feet = 0
