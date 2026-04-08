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
from reservoirs.reservoir import Reservoir
from source import usbr_rise
import colorado.lb as lb
import colorado.allb as all_b
from sheet import sheet
from typing import List
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from datetime import datetime

selenium_driver = None

class LakePleasant(Reservoir):
    def __init__(self):
        headers:List[str] = [lb.MOHAVE,  lb.MOHAVE_ELEVATION, lb.MOHAVE_INFLOW,
                             lb.MOHAVE_RELEASE,lb.MOHAVE_ELEVATION, lb.MOHAVE_EVAPORATION]
        super().__init__('Lake Pleasant', headers)

        self.get_lake_pleasant_data()

        # USGS 09426650 — Central Arizona Project Canal at Havasu Pumping Plant (near Parker, AZ)
        # USGS 09426700 — CAP Canal at MP 7.9 near Parker Dam, AZ
        # USGS 09427100 — CAP Canal at MP 162.3 at 7th St at Phoenix, AZ
        # USGS 09427300 — CAP Canal above Brady Pump Plant near Coolidge, AZ (further downstream, south of Phoenix toward Tucson).

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

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

        # Current
        #
        # self.elevation_feet = self.get_elevation(self.water_year)[1]
        # self.active_capacity_af = 0

        # usbr_lake_mohave_water_temperature_degf = 6132
        # usbr_lake_mohave_release_total_cfs = 6135

        # Inflow
        # usbr_blue_mesa_inflow_cfs = 4279
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_inflow_cfs, self.water_year, self.water_year,  title=ub.BLUE_MESA_INFLOW_WY, month=all_b.WY, divisor=1)

        # self.inflow_actual_af = self.get_value_by_year(self.water_year, lb.MOHAVE_INFLOW)
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

    def get_elevation(self, year, end_year:int|None =None)->float:
        usbr_lake_mohave_elevation_ft = 6133
        info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft, water_year_info=self.water_year_info,
                                                  alias=lb.MOHAVE_ELEVATION)
        sheet.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date', value_column_name=lb.MOHAVE_ELEVATION)
        return daily_elevation_ft[-1]

    def get_lake_pleasant_data(self):
        import os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

        options = Options()
        options.add_argument("--headless=new")  # Faster modern headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")
        # Do NOT disable images or JavaScript here — the data needs JS + iframes

        # Adjust path if needed: run `which chromedriver` to confirm
        service = Service("/usr/lib/chromium-browser/chromedriver")

        driver = None
        try:
            print("Starting Chromium on Jetson Orin...")
            driver = webdriver.Chrome(service=service, options=options)

            driver.set_page_load_timeout(90)
            driver.set_script_timeout(60)

            url = "https://www.cap-az.com/cap-system/water-operations/lake-pleasant/"
            print(f"Loading page: {url}")
            driver.get(url)

            # Wait for at least one iframe to load and for key text to appear
            print("Waiting for dynamic iframe content (Lake Pleasant data)...")
            wait = WebDriverWait(driver, 30)  # Up to 30 seconds
            wait.until(EC.any_of(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Water Surface Elevation"),
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            ))

            # Extra small wait for numbers to populate
            time.sleep(4)

            # Get full rendered text (including content from iframes if they injected)
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Fallback: switch into iframes if main body still misses the data
            if "Water Surface Elevation" not in page_text:
                print("Main body missing data — checking iframes...")
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        page_text += " " + driver.find_element(By.TAG_NAME, "body").text
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()

            data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "elevation_ft": None,
                "storage_acre_feet": None,
                "surface_area_acres": None,
                "percent_of_max": None,
            }

            # Improved regex patterns based on actual page text
            elev_match = re.search(r'Water Surface Elevation\s*[:\-]?\s*([0-9.]+)', page_text, re.IGNORECASE)
            if elev_match:
                data["elevation_ft"] = float(elev_match.group(1))
                self.elevation_feet = float(elev_match.group(1))

            storage_match = re.search(r'Storage Volume[:\s]*([0-9,]+(?:\.[0-9]+)?)', page_text, re.IGNORECASE)
            if storage_match:
                data["storage_acre_feet"] = float(storage_match.group(1).replace(',', ''))
                self.active_capacity_af = float(storage_match.group(1).replace(',', ''))

            area_match = re.search(r'Surface Area[:\s]*([0-9,]+(?:\.[0-9]+)?)', page_text, re.IGNORECASE)
            if area_match:
                data["surface_area_acres"] = float(area_match.group(1).replace(',', ''))

            # Better regex for "Percent of max (1,702): XX.X" or similar
            percent_match = re.search(r'Percent of max \(1,702\)\s*[:\-]?\s*([0-9.]+)', page_text, re.IGNORECASE)

            if percent_match:
                data["percent_of_max"] = float(percent_match.group(1))
            else:
                # Fallback if format varies slightly
                percent_match = re.search(r'Percent of max.*?[:\-]?\s*([0-9.]+)\s*%', page_text, re.IGNORECASE)
                if percent_match:
                    data["percent_of_max"] = float(percent_match.group(1))

            # Print results
            print(f"\n✅ Lake Pleasant Data as of {data['timestamp']}")
            if data['elevation_ft']:
                print(f"Water Surface Elevation : {data['elevation_ft']:.4f} feet")
            else:
                print("Elevation: Not found")

            if data['storage_acre_feet']:
                print(f"Storage Volume         : {data['storage_acre_feet']:,.2f} acre-feet")
            else:
                print("Storage: Not found")

            if data['surface_area_acres']:
                print(f"Surface Area           : {data['surface_area_acres']:,.2f} acres")
            else:
                print("Surface Area: Not found")

            if data['percent_of_max']:
                print(f"Percent of Max Capacity: {data['percent_of_max']}%")
            else:
                print("Percent: Not found")

            return data

        except TimeoutException:
            print("❌ Timeout waiting for Lake Pleasant data to load (iframes slow?)")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass