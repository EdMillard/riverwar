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
import copy
from datetime import date
from pathlib import Path
from api.reservoir import Reservoir
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from openpyxl import Workbook
import pandas as pd
from report.doc import Report
from sheet import sheet
from sheet.sheet import Sheet
from scipy.interpolate import interp1d
from source.water_year_info import WaterYearInfo
from source.usgs_gage import USGSGage
from source import usbr_rise
from typing import List
import warnings

class LakePowell(Reservoir):
    def __init__(self):
        super().__init__('Powell')

        self.start_year = 2026
        self.end_year = 2020
        self.headers:List[str] = [ub.POWELL, ub.POWELL_EVAPORATION, ub.POWELL_ELEVATION,
                                  ub.GLEN_CANYON, ub.INFLOW, ub.INFLOW_UNREGULATED]
        self.df: pd.DataFrame = sheet.create_df(self.start_year, self.end_year, self.headers)

        self.start_date = date(2026, 1, 1)
        self.end_date = date(2026, 12, 31)
        self.df_daily: pd.DataFrame = sheet.create_daily_df(self.start_date, self.end_date, self.headers)

        self.full_feet = 3700
        self.power_head_target_feet = 3510
        self.power_head_last_feet = 3500
        self.turbine_intake_feet = 3490
        self.dead_pool_feet = 3370

        self.usgs_release_gage_id:str = '09380000'
        self.dead_pool_af = 1_578_783

        self.full_af = LakePowell.af_for_elevation(self.full_feet)
        self.power_head_target_af = LakePowell.af_for_elevation(self.power_head_target_feet)
        self.power_head_last_af = LakePowell.af_for_elevation(self.power_head_last_feet)
        self.turbine_intake_af = LakePowell.af_for_elevation(self.turbine_intake_feet)
        self.dead_pool_af_2 = LakePowell.af_for_elevation(self.dead_pool_feet)
        self.now = LakePowell.af_for_elevation(self.dead_pool_feet)

        self.elevation(2026)
        self.release_usgs(2026)

        a3510 = get_lake_powell_capacity(3510.0, elev_col='Elevation_ft_NAVD88',
                                         cap_col='Capacity_acrefeet') - self.dead_pool_af
        a3500 = get_lake_powell_capacity(3500.0, elev_col='Elevation_ft_NAVD88',
                                         cap_col='Capacity_acrefeet') - self.dead_pool_af
        a3490 = get_lake_powell_capacity(3490.0, elev_col='Elevation_ft_NAVD88',
                                         cap_col='Capacity_acrefeet') - self.dead_pool_af
        now = get_lake_powell_capacity(3530.19, elev_col='Elevation_ft_NAVD88',
                                         cap_col='Capacity_acrefeet') - self.dead_pool_af
        deadpool = get_lake_powell_capacity(self.dead_pool_feet, elev_col='Elevation_ft_NAVD88',
                                         cap_col='Capacity_acrefeet') # - self.dead_pool_af
        now = get_lake_powell_capacity(3530.19, elev_col='Elevation_ft_NAVD88',
                                       cap_col='Capacity_acrefeet') - self.dead_pool_af
        pass
        # 7427162.58
        # 6315769.35
        # 5353021.28
        print(
            f'3530.19:\t{now:8,.0f}\n3510.00:\t{a3510:8,.0f}\t{now - a3510:8,.0f}\n3500.00:\t{a3500:8,.0f}\t{now - a3500:8,.0f}\n3490.00:\t{a3490:8,.0f}\t{now - a3490:8,.0f}')

        self.elevation(self.start_year)
        self.release_usgs(self.start_year)

    @staticmethod
    def af_for_elevation(feet):
        return get_lake_powell_capacity(feet, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet')

    def capacity_last(self, year, end_year:int|None =None):
        usbr_lake_powell_storage_af = 509
        sheet.usbr_get_last_value(usbr_lake_powell_storage_af, year)

    def elevation_last(self, year, end_year:int|None =None):
        usbr_lake_powell_elevation_af = 508
        sheet.usbr_get_last_value(usbr_lake_powell_elevation_af, year)

    def evaporation_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(self.df, usbr_lake_powell_evap_af, year, end_year,  title=ub.POWELL_EVAPORATION)

    def release_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_release_total_af = 4354
        sheet.usbr_annuals(self.df, usbr_lake_powell_release_total_af, year, end_year, title=ub.GLEN_CANYON)

    def regulated_inflow_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_regulated_inflow_af = 4288
        sheet.usbr_annuals(self.df, usbr_lake_powell_regulated_inflow_af, year, end_year, title=ub.INFLOW)

    def unregulated_inflow_annual(self, year, end_year:int|None =None):
        if end_year is None:
            end_year = year
        usbr_lake_powell_unregulated_inflow_af = 4301
        sheet.usbr_annuals(self.df, usbr_lake_powell_unregulated_inflow_af, year, end_year, title=ub.INFLOW_UNREGULATED)

    def capacity(self, year, end_year:int|None =None):
        pass

    @staticmethod
    def get_water_year_info(year:int):
        start_date = date(year, 1, 1)
        water_year_info = WaterYearInfo.get_water_year(start_date)
        return water_year_info

    def elevation(self, year, end_year:int|None =None):
        water_year_info = LakePowell.get_water_year_info(year)
        usbr_lake_powell_elevation_ft = 508
        info, daily_elevation_ft = usbr_rise.load(usbr_lake_powell_elevation_ft, water_year_info=water_year_info,
                                                  alias=ub.POWELL_ELEVATION)
        sheet.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date', value_column_name=ub.POWELL_ELEVATION)
        pass

    def evaporation(self, year, end_year:int|None =None):
        pass

    def release(self, year, end_year:int|None =None):
        pass

    def regulated_inflow(self, year, end_year:int|None =None):
        pass

    def unregulated_inflow(self, year, end_year:int|None =None):
        pass

    def release_usgs_annual(self, year, end_year:int|None =None):
        values = sheet.usgs_annuals(self.df, self.usgs_release_gage_id, 1955, end_year) # ub.LEES_FERRY_USGS

    def release_usgs(self, year, end_year:int|None =None):
        water_year_info = LakePowell.get_water_year_info(year)
        usgs_gage = USGSGage(self.usgs_release_gage_id, water_year_info)
        daily = usgs_gage.daily_discharge(water_year_info=water_year_info, alias=ub.LEES_FERRY_USGS)
        daily_clipped = Reservoir.clip_array_by_dates(daily, water_year_info.start_date, water_year_info.end_date)
        pass

    def copy(self):
        return copy.copy(self)

    def __str__(self) -> str:
        string = f" '\'{self.name}\'"

        return string

class Colorado_River_Ops(Sheet):
    def __init__(self):
        headers = [lb.MEAD_ELEVATION, ub.POWELL_ELEVATION, '1', lb.MEAD, ub.POWELL, ub.FLAMING_GORGE, ub.BLUE_MESA]
        super().__init__(headers, start_year=2026, end_year=2026)


    def load_df(self, df_compact : pd.DataFrame) -> None:
        df_len = len(self.df) + 2
        usbr_lake_mead_elevation_ft = 6123
        mead_elevation = sheet.usbr_get_last_value(usbr_lake_mead_elevation_ft, self.start_year)

        usbr_lake_mead_storage_af = 6124
        mead_storage = sheet.usbr_get_last_value(usbr_lake_mead_storage_af, self.start_year)

        usbr_lake_powell_elevation_af = 508
        powell_elevation = sheet.usbr_get_last_value(usbr_lake_powell_elevation_af, self.start_year)

        usbr_lake_powell_storage_af = 509
        powell_storage = sheet.usbr_get_last_value(usbr_lake_powell_storage_af, self.start_year)

        usbr_flaming_gorge_storage_af = 337
        flaming_gorge_storage = sheet.usbr_get_last_value(usbr_flaming_gorge_storage_af, self.start_year)

        usbr_blue_mesa_storage_af = 76
        blue_mesa_storage = sheet.usbr_get_last_value(usbr_blue_mesa_storage_af, self.start_year)

        pass

    def build_sheet(self)-> None:
        # self.set_bg(lb.MX_TREATY, ub.GLEN_CANYON_RELEASE, color=all_b.USBR_AR_FLOW)

        self.format_header()

        self.set_column_width(lb.MEAD_ELEVATION, 5, to=ub.POWELL_ELEVATION)
        self.set_column_width(lb.MEAD, 7, to=ub.BLUE_MESA)


def run():
    # Elevation_ft_NAVD88,Elevation_ft_NGVD29,Area_acres,Capacity_acrefeet
    lake_powell = LakePowell()
    deadpool = 1_578_783

    a3510 = get_lake_powell_capacity(3510.0, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    a3500 = get_lake_powell_capacity(3500.0, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    a3490 = get_lake_powell_capacity(3490.0, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    now = get_lake_powell_capacity(3530.19, elev_col='Elevation_ft_NAVD88', cap_col='Capacity_acrefeet') - deadpool
    print(f'3530.19:\t{now:8,.0f}\n3510.00:\t{a3510:8,.0f}\t{now-a3510:8,.0f}\n3500.00:\t{a3500:8,.0f}\t{now-a3500:8,.0f}\n3490.00:\t{a3490:8,.0f}\t{now-a3490:8,.0f}')

    river_ops = Colorado_River_Ops()
    file_path = Path('excel/Colorado_River_Ops.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        river_ops.export(writer, all_b.OPERATIONS, None, number_format='#,##0;-#,##0')

        wb: Workbook = writer.book
        wb.calcMode = "auto"  # ensure automatic calculation

    Report.open_docx_in_app(file_path)


def get_lake_powell_capacity(
    elevation_ft: float,
    csv_path: str = "data/Colorado_River/Lake_Powell_2018_ElevAreaCap_interp.csv",  # <-- update this
    elev_col: str = "elevation",      # adjust if column name differs (check your CSV)
    cap_col: str = "capacity_af",     # adjust if needed (often "storage" or "capacity")
    navd88: bool = True               # reminder: elevations must be NAVD 88
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


if __name__ == "__main__":
    run()