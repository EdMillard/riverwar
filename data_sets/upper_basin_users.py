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
import datetime
from data_sets.data_set import DataSet
from api import df_utils
import colorado.ub as ub
import colorado.allb as all_b
import pandas as pd
from typing import Optional
from reservoirs.strawberry import Strawberry
from reservoirs.starvation import Starvation
from reservoirs.heron import Heron
from sheet import sheet
from source import cdss
from source.water_year_info import WaterYearInfo
from pathlib import Path


class UpperBasinUsersDataSet(DataSet):
    def __init__(self, name:str, month:int=10):
        super().__init__(name, month=month)
        my_source_path:Path = Path(__file__)
        csv_path:Path = DataSet.csv_path(name)
        if csv_path.exists():
            csv_mod_date:datetime.datetime = UpperBasinUsersDataSet.file_mod_date(csv_path)
            my_mod_date:datetime.datetime = UpperBasinUsersDataSet.file_mod_date(my_source_path)
            if my_mod_date > csv_mod_date:
                print('need update')
                csv_path.unlink()
        self.df = self.from_csv(name)

    @staticmethod
    def file_mod_date(path: Path)->datetime.datetime:
        if path.exists():
            timestamp = path.stat().st_mtime
            # convert time to dd-mm-yyyy hh:mm:ss
            m_time = datetime.datetime.fromtimestamp(timestamp)
            return m_time
        else:
            return datetime.datetime.min

    def load(self) -> Optional[pd.DataFrame]:
        start_year = 1971
        end_year = 2026

        df: pd.DataFrame = df_utils.create_df(start_year, end_year, [])

        UpperBasinUsersDataSet.upper_basin_from_api(df, start_year, end_year)

        # df_utils.add_column_sum(df, [])
        return df

    @staticmethod
    def upper_basin_from_api(df: pd.DataFrame, start_year:int, end_year:int):

        # UT
        # UT Starvation
        starvation = Starvation()
        starvation.load_data_annual()
        # df_utils.copy_column(strawberry.df_annual, df, 'Starvation')

        # UT Strawberry
        strawberry = Strawberry()
        strawberry.load_data_annual()
        df_utils.copy_column(strawberry.df_annual, df, 'Strawberry')

        # UT / Wasatch Front
        # Need to find data for this tunnel to Provo River since USGS discontinued theirs in 1969, Utah DWRi, Provo River WUA
        # sheet.usgs_annuals(df, '09272500', 1954, 1969, month=all_b.WY, divisor=1, title='Duchesne Tunnel')
        # sheet.usgs_annuals(df, '09282000', start_year, end_year, month=all_b.WY, divisor=1, title='Old Strawberry Tunnel')
        # sheet.usgs_annuals(df, '10149400', 2002, end_year, month=all_b.WY, divisor=1, title='Above Strawberry Tunnel')
        # sheet.usgs_annuals(df, '10149500', 1989, end_year, month=all_b.WY, divisor=1, title='Below Strawberry Tunnel')
        # df_utils.subtract_columns_by_year(df, 'Above Strawberry Tunnel', 'Strawberry Tunnel', [(df, 'Below Strawberry Tunnel')])
        # (The older Strawberry Tunnel had a historical USGS gage — 09282000 at the West Portal — but it's long retired/inactive.)How to Monitor the DiversionYou calculate or estimate diverted/augmented flows by comparing gages above and below the release points, or by subtracting natural inflows:Key USGS gages:10149000 — Sixth Water Creek above Syar Tunnel (monitors natural flow above the system).
        #     10149400 — Diamond Fork above Red Hollow near Thistle (primary gage for instream flows and augmented discharge from the system; heavily referenced for CUPCA-mandated minimums).
        #     10149500 — Diamond Fork below Red Hollow near Thistle (helps show changes post-release).
        # sheet.usgs_annuals(df, ub.USGS_UT_JORDAN_RIVER_GAGE, start_year, end_year, month=all_b.WY, divisor=1, title=ub.USGS_UT_JORDAN_RIVER)

        # CDSS
        # ===============================================================
        # Northern Water
        #
        # Adams Tunnel: ADATUNCO
        wdid = '0404634'
        # info = cdss.structure_info(wdid)
        # class_info = cdss.water_class_info(wdid)
        # 10404634 Total (Diversion) this seems to be Release delayed by a year
        # cdss_annuals(df, wdid, 2011, end_year, water_class_num='10404634', title=ub.USGS_CO_ADAMS_TUNNEL_DIVERSION, divisor=1)
        # 20404634 Total (Release)
        cdss_annuals(df, wdid, 1994, end_year, water_class_num='20404634', title=ub.CO_NORTHERN_WATER, divisor=1)
        sheet.usgs_annuals(df, ub.USGS_CO_ADAMS_TUNNEL_GAGE, start_year, 1993, divisor=1, month=all_b.WY, title=ub.CO_NORTHERN_WATER)

        # ===============================================================
        # Fryark
        #
        # Boustead Tunnel: BOUTUNCO
        # info = cdss.structure_info('1104615')
        # class_info = cdss.water_class_info('1104615')
        wdid = '1104615'
        #     154205  365 2021-10-01T00:00:00 2022-09-30T00:00:00  '1104615 S:4 F:3804625 U:Q T:7 G: To:1103500.020'
        #     143815  365 2021-10-01T00:00:00 2022-09-30T00:00:00  '1104615 S:X F: U:Q T:0 G: To:'
        #   11104615  365 2021-10-01T00:00:00 2022-09-30T00:00:00  '1104615 Total (Diversion)'
        #   21104615  365 2021-10-01T00:00:00 2022-09-30T00:00:00  '1104615 Total (Release)'
        cdss_annuals(df, wdid, 2014, end_year, water_class_num='143815', title=ub.CDSS_CO_BOUSTEAD_TUNNEL, divisor=1)
        # cdss_annuals(df, wdid, 2017, end_year, water_class_num='11104615', title=ub.CDSS_CO_BOUSTEAD_TUNNEL_DIVERSION, divisor=1)
        # cdss_annuals(df, wdid, 2017, end_year, water_class_num='21104615', title=ub.CDSS_CO_BOUSTEAD_TUNNEL_RELEASE, divisor=1)
        # Water quality only
        # sheet.usgs_annuals(df, ub.USGS_CO_BOUSTEAD_TUNNEL_GAGE, start_year, end_year, divisor=1, month=all_b.WY, title=ub.USGS_CO_BOUSTEAD_TUNNEL)

        # ===============================================================
        # Denver Water
        #
        # MOFTUNCO, Moffat Tunnel
        wdid = '0604655'
        # info = cdss.structure_info(wdid)
        # class_info = cdss.water_class_info(wdid)
        # 10604655 Diversion
        cdss_annuals(df, wdid, 2011, end_year, water_class_num='10604655', title='Moffat Tunnel Diversion CDSS', divisor=1)
        # 20604655 Release
        cdss_annuals(df, wdid, 2011, end_year, water_class_num='20604655', title='Moffat Tunnel Release CDSS', divisor=1)
        sheet.usgs_annuals(df, ub.USGS_CO_MOFFAT_TUNNEL_GAGE, start_year, end_year, divisor=1, month=all_b.WY, title=ub.USGS_CO_MOFFAT_TUNNEL)

        # ROBTUNCO
        wdid = '8000653'
        # info = cdss.structure_info(wdid)
        # class_info = cdss.water_class_info(wdid)
        # Diversion
        # cdss_annuals(df, wdid, 1993, end_year, water_class_num='18000653', title=ub.CDSS_CO_ROBERTS_TUNNEL, divisor=1)
        # Release
        cdss_annuals(df, wdid, 1974, end_year, water_class_num='28000653', title=ub.CDSS_CO_ROBERTS_TUNNEL, divisor=1)
        # sheet.usgs_annuals(df, ub.USGS_CO_ROBERTS_TUNNEL_GAGE, start_year, end_year, divisor=1, title=ub.USGS_CO_ROBERTS_TUNNEL)

        # HOMTUNCO, Homestake Tunnel/Aurora
        wdid = '1104613'
        # info = cdss.structure_info(wdid)
        #      95612  215 1978-10-01T00:00:00 1979-09-30T00:00:00  '1104613 S:4 F: U:1 T: G: To:'
        #   11104613  215 1978-10-01T00:00:00 1979-09-30T00:00:00  '1104613 Total (Diversion)'
        cdss_annuals(df, wdid, start_year, 1987, water_class_num='11104613', title=ub.CDSS_CO_HOMESTAKE_TUNNEL, divisor=1, analyze=False)
        cdss_annuals(df, wdid, 2014, 2015, water_class_num='11104613', title=ub.CDSS_CO_HOMESTAKE_TUNNEL, divisor=1, analyze=False)
        cdss_annuals(df, wdid, 2016, 2016, title=ub.CDSS_CO_HOMESTAKE_TUNNEL, divisor=1, analyze=True)
        cdss_annuals(df, wdid, 2020, end_year, title=ub.CDSS_CO_HOMESTAKE_TUNNEL, divisor=1, analyze=True)
        sheet.usgs_annuals(df, ub.USGS_CO_HOMESTAKE_TUNNEL_GAGE, 1972, end_year, divisor=1, title=ub.USGS_CO_HOMESTAKE_TUNNEL)

        # TWITUNCO, Independence Pass/Twin Lakes Tunnel, Colorado Springs, Pueblo, Aurora
        #      95822  362 1972-10-01T00:00:00 1973-09-30T00:00:00  '1104617 S:4 F: U:1 T: G: To:'
        #      95241   15 1973-09-16T00:00:00 1973-09-30T00:00:00  '1104617 S:4 F: U:9 T: G: To:'
        #      95823  304 1972-12-01T00:00:00 1973-09-30T00:00:00  '1104617 S:4 F: U:Q T: G: To:'
        #   11104617  362 1972-10-01T00:00:00 1973-09-30T00:00:00  '1104617 Total (Diversion)'
        wdid = '1104617'
        cdss_annuals(df, wdid, start_year, 1987, title='Twin Lakes', divisor=1, analyze=True)
        cdss_annuals(df, wdid, 2014, end_year, water_class_num='11104617', title='Twin Lakes', divisor=1, analyze=False)

        # VIDTUNCO, Vidler Tunnel, Golden
        #      66117    9 1979-07-01T00:00:00 1979-07-10T00:00:00  '0704626 S:4 F:0702501 U:Q T:7 G: To:'
        #      66116   91 1979-07-01T00:00:00 1979-09-30T00:00:00  '0704626 S:4 F:3604626 U:Q T:7 G: To:'
        #   10704626   91 1979-07-01T00:00:00 1979-09-30T00:00:00  '0704626 Total (Diversion)'
        #   20704626   91 1979-07-01T00:00:00 1979-09-30T00:00:00  '0704626 Total (Release)'
        wdid = '0704626'    # Active, historical 3604656, 3607211, 3608013
        cdss_annuals(df, wdid, 1977, end_year, water_class_num='10704626', title='Vidler', divisor=1, analyze=False)

        # GRNDRDCO, Gramd River Ditch to Cache La Poudre
        #      49815   31 1975-10-01T00:00:00 1975-10-31T00:00:00  '5104601 S:1 F: U:1 T: G: To:'
        #      49600  147 1976-05-01T00:00:00 1976-09-24T00:00:00  '5104601 S:1 F: U:T T: G: To:'
        #   15104601  178 1975-10-01T00:00:00 1976-09-24T00:00:00  '5104601 Total (Diversion)'
        wdid = '5104601'  # Release 0304601
        cdss_annuals(df, wdid, 1976, end_year, water_class_num='15104601', title='Grand River Ditch', divisor=1, analyze=False)

        # CO / West Slope Reservoirs
        #
        # ID=ILRESCO, Dillon
        # ID=HOMRESCO&MTYPE=STORAGE, Homestake
        # ID=GRARESCO&MTYPE=STORAGE, Granby
        # ID=GRERESCO&MTYPE=STORAGE Green Mountain
        # ID=RIFRESCO&MTYPE=STORAGE Rifle Gap
        # ID=RUERESCO&MTYPE=STORAGE Ruedi
        # ID=SHARESCO&MTYPE=STORAGE Shadow Mountain
        # ID=WLFRESCO&MTYPE=STORAGE Williams Fork
        # ID=WILRESCO&MTYPE=STORAGE Willow Creek
        # https://www.northernwater.org/WaterProjects/WestSlopeWaterData.aspx?WDType=R Windy Gap
        # USGS Wolford Mountain 09041395
        # ID=BLURESCO&MTYPE=STORAGE Upper Bluw
        # https://nwis.waterdata.usgs.gov/nwis/uv?09096100 Vega

        # NM / San Juan Chama
        heron = Heron()
        heron.load_data_annual()
        df_utils.copy_column(heron.df_annual, df, ub.USBR_NM_SAN_JUAN_CHAMA_TUNNEL_AF)


def cdss_annuals(df: pd.DataFrame, wdid:str,  start_year:int, end_year:int, water_class_num:str='', title:str='',
                 month:int=10, divisor:int=1, analyze:bool=False):
    annuals = []
    values = []
    for year in range(start_year, end_year + 1):
        if month != 1:
            ts = pd.Timestamp(f'{year - 1}-{month}-01 00:00:00')
        else:
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
        water_year_info = WaterYearInfo.get_water_year(ts, month=month)
        daily_af = cdss.structures_divrec(None, wdid, water_year_info, water_class_num=water_class_num, analyze=analyze)
        if daily_af is None:
            continue
        annual_af = cdss.daily_to_water_year(daily_af)
        if len(annual_af) == 1:
            values.append(annual_af[0][1] / divisor)
            annuals.append(annual_af[0])
            update_value_by_year(df, annual_af[0], title)
        elif annual_af is None:
            print(f'No years returned {wdid} {year}')
        elif len(annual_af) == 0:
            print(f'cdss_annuals no years returned  {wdid} {year}')
            values.append(0)
        else:
            print(f'cdss_annuals multiple years returned  {wdid} {year} {annual_af}')

def update_value_by_year(df: pd.DataFrame, year_value_tuple: tuple, target_column: str):
    """
    Update or add a value for a specific year in-place.

    Example: update_value_by_year(df, (2014, 204511.0), 'SomeFlow_cfs')
    """
    year, value = year_value_tuple

    # Find if the year already exists
    mask = df['Year'] == year

    if mask.any():
        # Update existing row (in-place)
        df.loc[mask, target_column] = value
    else:
        # Create new row if year doesn't exist
        new_row = pd.DataFrame({'Year': [year], target_column: [value]})
        # Add any other columns as NaN if needed
        for col in df.columns:
            if col not in new_row.columns:
                new_row[col] = pd.NA

        df = pd.concat([df, new_row], ignore_index=True)

    return df  # even if in-place, returning is good practice