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
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
import pandas as pd
from sheet import sheet
from sheet.sheet import Sheet
from sheet.sheet import cl, cn

'''
    usbr_flaming_gorge_storage_af = 337
    # usbr_flaming_gorge_inflow_unregulated_cfs = 338
    usbr_flaming_gorge_inflow_cfs = 339
    # usbr_flaming_gorge_elevation_ft = 341
    usbr_flaming_gorge_evaporation_af = 342
    # usbr_flaming_gorge_bank_storage_af = 4275
    # usbr_flaming_gorge_inflow_af = 4287
    # usbr_flaming_gorge_inflow_volume_unregulated_af = 4300
    # usbr_flaming_gorge_release_powerplant_cfs = 4306
    usbr_flaming_gorge_release_total_cfs = 4314
    # usbr_flaming_gorge_release_total_af = 4353
    # usbr_flaming_gorge_release_powerplant_af = 4360
    # usbr_flaming_gorge_release_spillway_cfs = 4371
    # usbr_flaming_gorge_release_bypass_cfs = 4390
    # usbr_flaming_gorge_change_in_storage_af = 4402
    # usbr_flaming_gorge_area_acres = 4782
    
    usbr_blue_mesa_storage_af = 76
    # usbr_blue_mesa_elevation_ft = 78
    usbr_blue_mesa_evaporation_af = 79
    usbr_blue_mesa_inflow_cfs = 4279
    # usbr_blue_mesa_inflow_af = 4283
    # usbr_blue_mesa_inflow_unregulated_cfs = 4295
    # usbr_blue_mesa_inflow_volume_unregulated_af = 4297
    # usbr_blue_mesa_release_powerplant_cfs = 4302
    usbr_blue_mesa_release_total_cfs = 4310
    # usbr_blue_mesa_release_total_af = 4349
    # usbr_blue_mesa_release_powerplant_af = 4361
    # usbr_blue_mesa_release_spillway_cfs = 4380
    # usbr_blue_mesa_release_bypass_cfs = 4381
    # usbr_blue_mesa_release_bypass_af = 4382
    # usbr_blue_mesa_change_in_storage_af = 4398
    # usbr_blue_mesa_area_acres = 4773
'''

class Reservoirs(Sheet):
    def __init__(self):
        headers = [lb.HAVASU, lb.MEAD, ub.POWELL, ub.FLAMING_GORGE, ub.BLUE_MESA,
                   lb.MEAD_EVAPORATION, ub.POWELL_EVAPORATION,
                   lb.MEAD_ELEVATION, ub.POWELL_ELEVATION]
        super().__init__(headers)

    def load_df(self, df_compact : pd.DataFrame) -> None:
        # Active Capacity
        usbr_lake_havasu_storage_af = 6128
        sheet.usbr_last_value(self.df, usbr_lake_havasu_storage_af, self.start_year, self.end_year, title=lb.HAVASU, month=10)

        usbr_lake_mead_storage_af = 6124
        sheet.usbr_last_value(self.df, usbr_lake_mead_storage_af, self.start_year, self.end_year, title=lb.MEAD, month=10)

        usbr_lake_powell_storage_af = 509
        sheet.usbr_last_value(self.df, usbr_lake_powell_storage_af, self.start_year, self.end_year,  title=ub.POWELL)

        usbr_flaming_gorge_storage_af = 337
        sheet.usbr_last_value(self.df, usbr_flaming_gorge_storage_af, self.start_year, self.end_year,  title=ub.FLAMING_GORGE)

        usbr_blue_mesa_storage_af = 76
        sheet.usbr_last_value(self.df, usbr_blue_mesa_storage_af, 1967, self.end_year,  title=ub.BLUE_MESA)

        # Evap
        usbr_lake_mohave_evap_af = 1776
        # https://www.usbr.gov/pn-bin/hdb/hdb.pl?svr=lchdb&sdi=1776&tstp=DY&t1=2024-02-05T00:00&t2=2026-03-07T00:00&table=R&mrid=0&format=csv

        usbr_lake_mohave_evap_af = 1777
        # https://www.usbr.gov/pn-bin/hdb/hdb.pl?svr=lchdb&sdi=1777&tstp=DY&t1=2024-01-01T00:00&t2=2026-03-07T00:00&table=R&format=csv
        # sheet.usbr_annuals(self.df, usbr_lake_havasu_evap_af, 2010, self.end_year, title=lb.HAVASU_EVAPORATION)

        usbr_lake_havasu_evap_af = 1778
        # sheet.usbr_annuals(self.df, usbr_lake_havasu_evap_af, 2010, self.end_year,  title=lb.HAVASU_EVAPORATION)
        # https://www.usbr.gov/pn-bin/hdb/hdb.pl?svr=lchdb&sdi=1778&tstp=DY&t1=2024-01-01T00:00&t2=2026-03-07T00:00&table=R&format=csv

        df_mead_evap = sheet.read_csv('data/Colorado_River/mead_evap.csv', sep=',')
        sheet.merge_annual_column(self.df, df_mead_evap, lb.MEAD_EVAPORATION, inp_column_name='Evaporation_AcreFeet')

        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(self.df, usbr_lake_powell_evap_af, self.start_year, self.end_year,  title=ub.POWELL_EVAPORATION)

        # Elevation
        usbr_lake_mead_elevation_ft = 6123
        sheet.usbr_last_value(self.df, usbr_lake_mead_elevation_ft, self.start_year, self.end_year, title=lb.MEAD_ELEVATION, divisor=1)

        usbr_lake_powell_elevation_af = 508
        sheet.usbr_last_value(self.df, usbr_lake_powell_elevation_af, 1965, self.end_year, title=ub.POWELL_ELEVATION, divisor=1)


    def build_sheet(self) -> None:
        ws = self.ws

        self.set_bg(lb.HAVASU, to=ub.BLUE_MESA, color=all_b.USBR_RISE_ACTIVE_CAPACITY_BG)
        self.set_bg(lb.MEAD_EVAPORATION, to=ub.POWELL_EVAPORATION, color=all_b.EVAPORATION_BG)
        self.set_bg(lb.MEAD_ELEVATION, to=ub.POWELL_ELEVATION, color=all_b.USBR_RISE_ELEVATION_BG)

        self.format_header()
