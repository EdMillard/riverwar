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
import copy
from datetime import date
from api import df_utils
from reservoirs.reservoir import Reservoir
from source.usgs_gage import USGSGage
import colorado.ub as ub
import colorado.lb as lb
import colorado.allb as all_b
from sheet import sheet
from typing import List, Optional
import pandas as pd
from scipy.interpolate import interp1d
import warnings

# https://www.cbrfc.noaa.gov/dbdata/station/espgraph/espgraph_hc.html?id=GLDA3&year=2026
class LakePowell(Reservoir):
    def __init__(self, upstream:Optional[List[Reservoir]]=None):
        headers:List[str] = [ub.POWELL_WY, ub.POWELL_MOST, ub.POWELL_ABOVE_3500,
                             ub.POWELL_EVAPORATION_WY, ub.POWELL_ELEVATION_WY,
                             ub.GLEN_CANYON_WY,
                             ub.POWELL_INFLOW, ub.POWELL_INFLOW_CFS,
                             ub.POWELL_INFLOW_UNREGULATED, ub.POWELL_INFLOW_UNREGULATED_CFS,
                             ub.POWELL_RELEASE, ub.POWELL_RELEASE_CFS]
        super().__init__('Lake Powell', headers, catalog_id = 2362, upstream=upstream)


        self.start_year = 1964
        self.usgs_release_gage_id:str = '09380000'

        self.usbr_rise_inflow_unregulated_af_id = self.usbr_item_ids.get('inflow_volume_unregulated_af', 0)
        self.usbr_rise_inflow_unregulated_cfs_id = self.usbr_item_ids.get('inflow_unregulated_cfs', 0)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 3370
        self.dead_pool_af = LakePowell.get_capacity(self.dead_pool_feet)
        # Old commonly used number
        self.dead_pool_af = 1_578_783
        # self.active_capacity_af_chart = self.af_for_elevation(self.elevation_feet)

        self.full_feet = 3702.91
        self.full_af = self.af_for_elevation(self.full_feet)

        # Critical
        self.power_head_target_feet = 3510
        self.power_head_target_af = self.af_for_elevation(self.power_head_target_feet)

        self.power_head_min_feet = 3500
        self.power_head_min_af = self.af_for_elevation(self.power_head_min_feet)

        self.turbine_intake_feet = 3490.0
        self.turbine_intake_af = self.af_for_elevation(self.turbine_intake_feet)
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

    def load_data(self, report_path:Path, start_date:date, current_date:date, end_date:date):
        self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.POWELL_ELEVATION_WY)
        self.active_capacity_af = self.get_storage(self.usbr_rise_storage_af_id, ub.POWELL_WY)  # 1964

        self.evao_af = self.get_daily_and_last(self.usbr_rise_evap_af_id, ub.POWELL_EVAPORATION_WY)
        self.inflow_cfs = self.get_daily_and_last(self.usbr_rise_inflow_cfs_id, ub.POWELL_INFLOW_CFS)
        # self.inflow_af = self.get_daily_and_last(self.usbr_rise_inflow_af_id, ub.POWELL_INFLOW)
        self.inflow_unregulated_cfs = self.get_daily_and_last(self.usbr_rise_inflow_unregulated_cfs_id, ub.POWELL_INFLOW_UNREGULATED_CFS)
        # self.inflow_unregulated_af = self.get_daily_and_last(self.usbr_rise_inflow_unregulated_af_id, ub.POWELL_INFLOW_UNREGULATED)

        self.release_cfs = self.get_daily_and_last(self.usbr_rise_release_cfs_id, ub.POWELL_RELEASE_CFS)
        # self.release_af = self.get_daily_and_last(self.usbr_rise_release_af_id, ub.POWELL_RELEASE)

        # 24 Month
        #
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Unregulated Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        self.gap_water_parts = [
            ("Cut Release", 1480000, lb.PHX_COLOR),
            ("Cut Powell", 300000, lb.PINAL_COLOR),
            ("DROA", 1000000, lb.TUCSON_COLOR)
        ]

        # Actual from USBR/USGS
        headers_24_month = list(self.df_24_month.columns.astype(str))
        df: pd.DataFrame = df_utils.create_monthly_df(self.water_year_info.start_date, self.water_year_info.end_date,
                                                   headers_24_month)
        Reservoir.usbr_monthly(df, self.usbr_rise_inflow_af_id, self.water_year, "Regulated Inflow", month=all_b.WY)
        Reservoir.usbr_monthly(df, self.usbr_rise_release_af_id, self.water_year, "Total Release", month=all_b.WY)
        Reservoir.usbr_monthly(df, self.usbr_rise_evap_af_id, self.water_year, "Evaporation Losses", month=all_b.WY)

        Reservoir.usbr_end_of_month(df, self.usbr_rise_elevation_ft_id, self.water_year,
                                    "Reservoir Elevation End of Month ft", month=all_b.WY)
        Reservoir.usbr_end_of_month(df, self.usbr_rise_storage_af_id, self.water_year, "End Of Month Storage",
                                    month=all_b.WY)

        # self.df_monthly = df
        # df_diff = df_utils.subtract_dataframes(self.df_monthly, self.df_24_month)

        df_utils.subtract_constant(self.df_daily, ub.POWELL_WY, ub.POWELL_ABOVE_3500, self.power_head_min_af)
        self.get_projection(self.df_24_month, ub.POWELL_MOST)


    def af_for_elevation(self, feet:float|int):
        return LakePowell.get_capacity(feet, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - self.dead_pool_af

    def capacity_last(self, year, end_year:int|None =None):
        usbr_lake_powell_storage_af = 509
        sheet.usbr_get_last_value(usbr_lake_powell_storage_af, year, month=all_b.WY)

    def elevation_last(self, year, end_year:int|None =None):
        usbr_lake_powell_elevation_af = 508
        sheet.usbr_get_last_value(usbr_lake_powell_elevation_af, year)

    def evaporation_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(self.df, usbr_lake_powell_evap_af, year, end_year,  title=ub.POWELL_EVAPORATION_WY, month=all_b.WY)

    def release_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_release_total_af = 4354
        sheet.usbr_annuals(self.df, usbr_lake_powell_release_total_af, year, end_year, title=ub.GLEN_CANYON_WY, month=all_b.WY)

    def regulated_inflow_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_regulated_inflow_af = 4288
        sheet.usbr_annuals(self.df, usbr_lake_powell_regulated_inflow_af, year, end_year, title=ub.INFLOW_WY, month=all_b.WY)

    def unregulated_inflow_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_unregulated_inflow_af = 4301
        sheet.usbr_annuals(self.df, usbr_lake_powell_unregulated_inflow_af, year, end_year, title=ub.INFLOW_UNREGULATED_WY, month=all_b.WY)

    def release_usgs_annual(self, year, end_year:int|None =None):
        values = sheet.usgs_annuals(self.df, self.usgs_release_gage_id, 1955, end_year) # ub.LEES_FERRY_USGS_WY

    def release_usgs(self, year)->float:
        usgs_gage = USGSGage(self.usgs_release_gage_id, self.water_year_info)
        daily = usgs_gage.daily_discharge(water_year_info=self.water_year_info, alias=ub.GLEN_CANYON_WY)
        return daily[-1]

    def copy(self):
        return copy.copy(self)

    def __str__(self) -> str:
        string = f" '\'{self.name}\'"

        return string

    @staticmethod
    def get_capacity(
            elevation_ft: float,
            csv_path: str = "data/Colorado_River/Lake_Powell_2018_ElevAreaCap_interp.csv",  # <-- update this
            elev_col: str = "Elevation_ft_NAVD88",  # adjust if column name differs (check your CSV)
            cap_col: str = "Capacity_acrefeet",  # adjust if needed (often "storage" or "capacity")
            navd88: bool = True  # reminder: elevations must be NAVD 88
    ) -> float:
        """
        Returns active storage capacity in acre-feet for a given elevation (ft NAVD 88)
        using the USGS 2018 Lake Powell elevation-area-capacity table (interpolated preferred).

        Example usage:
            capacity = get_lake_powell_capacity(3650.5)
            print(f"At 3650.5 ft: {capacity:,.0f} af")
        """
        if not navd88:
            warnings.warn("Elevations should be in NAVD 88 datum per 2018 USGS data.")

        # Load the CSV (skip any header rows if needed; inspect your file)
        df = pd.read_csv(csv_path)

        # Assume columns are something like: elevation_ft, area_acres, capacity_af
        # Rename for consistency if needed
        df = df.rename(columns={
            elev_col: 'elevation_ft',
            cap_col: 'capacity_af'
        })

        # Sort by elevation (should already be sorted, but ensure)
        df = df.sort_values('elevation_ft').dropna(subset=['elevation_ft', 'capacity_af'])

        if elevation_ft < df['elevation_ft'].min() or elevation_ft > df['elevation_ft'].max():
            raise ValueError(
                f"Elevation {elevation_ft} ft is outside table range "
                f"({df['elevation_ft'].min():.2f} to {df['elevation_ft'].max():.2f} ft)"
            )

        # Create linear interpolator (capacity as function of elevation)
        interpolator = interp1d(
            df['elevation_ft'],
            df['capacity_af'],
            kind='linear',
            fill_value="extrapolate"  # but we already checked bounds
        )

        capacity = interpolator(elevation_ft)

        return float(capacity)
