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
from data_sets.data_set import DataSet
from sheet import sheet
from api import df_utils
import colorado.lb as lb
import colorado.allb as all_b
import pandas as pd
from typing import Optional
from colorado.lb_mainstream_cul import LBMainstreamCUL
from colorado.lb_reservoir_cul import LBReservoirCUL
from colorado.lb_tributary_cul import LBTributaryCUL

class LowerBasinCULDataSet(DataSet):
    def __init__(self, name:str, month:int=10):
        super().__init__(name, month=month)
        self.show_tributaries = True

        self.df = self.from_csv(name)

    def load(self) -> Optional[pd.DataFrame]:
        start_year = 1971
        end_year = 2024

        df: pd.DataFrame = df_utils.create_df(start_year, end_year, [])

        lb_mainstream_cul = LBMainstreamCUL(all_b.LB_MAINSTEM_CUL_SHEET)
        lb_mainstream_cul.load_df(df)

        # Lower Basin Reservoir Evap
        lb_reservoirs_cul = LBReservoirCUL(all_b.LB_RESERVOIRS_CUL_SHEET)
        lb_reservoirs_cul.load_df(df)
        df_utils.add_column_sum(lb_reservoirs_cul.df,
                                [lb.LAKE_MEAD_CUL, lb.LAKE_MOHAVE_CUL, lb.LAKE_HAVASU_CUL,
                                 lb.SENATOR_WASH_CUL, lb.DIVERSION_DAMS_CUL],
                                lb.LB_RESERVOIR_EVAP) # This is lb.LC_RESERVOIR_TOTAL_CUL in sheet, should get rid of one of these

        # California - Imperial Valley
        sheet.usgs_annuals(lb_mainstream_cul.df, '10254730', start_year, end_year, title=lb.ALAMO_RIVER,
                           divisor=1)
        sheet.usgs_annuals(lb_mainstream_cul.df, '10255550', start_year, end_year, title=lb.NEW_RIVER,
                           divisor=1)
        sheet.usgs_annuals(lb_mainstream_cul.df, '10259540', start_year, end_year, title=lb.WHITEWATER,
                           divisor=1)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.ALAMO_RIVER, lb.NEW_RIVER, lb.WHITEWATER], lb.SALTON_INFLOW)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_imperial_irrigation_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.IMPERIAL_CU, divisor=1)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_coachella_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.COACHELLA_CU, divisor=1)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.IMPERIAL_CU, lb.COACHELLA_CU], lb.IMPERIAL_VALLEY_CU)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_metropolitan_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.METROPOLITAN_CU, divisor=1)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_palo_verde_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.PALO_VERDE_CU, divisor=1)

        df_cu = sheet.read_csv('data/USBR_Reports/az/usbr_az_crit_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.AZ_CRIT_CU, divisor=1)

        df_cu = sheet.read_csv('data/USBR_Reports/az/usbr_az_wellton_mohawk_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.WELLTON_MOHAWK_CU, divisor=1)

        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.CA_M_I_OTHER, lb.CA_AGRICULTURE], lb.CA_MAINSTEM)

        df_utils.subtract_column(lb_mainstream_cul.df, lb.CA_OUTSIDE_SYSTEM, lb.IMPERIAL_VALLEY_CU,
                                 lb.CA_OUTSIDE_SYSTEM)
        df_utils.subtract_column(lb_mainstream_cul.df, lb.IMPERIAL_VALLEY_CU, lb.SALTON_INFLOW, lb.IMPERIAL_VALLEY_CU)

        # Mexico
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_mx, lb.MEXICO, divisor=1)

        # California continued
        df_utils.add_column_sum(lb_mainstream_cul.df,
                                [lb.CA_OUTSIDE_SYSTEM, lb.CA_MAINSTEM, lb.SALTON_INFLOW, lb.IMPERIAL_VALLEY_CU],
                                lb.CA_TOTAL)

        # Nevada
        lb_tributary_cul = None
        if self.show_tributaries:
            lb_tributary_cul = LBTributaryCUL(all_b.LB_TRIBUTARY_CUL_SHEET)
            lb_tributary_cul.load_df(df)
            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.NV_VIRGIN_CUL,
                                     lb.NV_MUDDY_CUL,
                                     lb.NV_TRIB_ABOVE_LAKE_MEAD_CUL],
                                    lb.NV_TRIBUTARY_CUL)

        df_utils.add_columns_across_dfs([(lb_mainstream_cul.df, lb.NV_M_I_OTHER),
                                         (lb_mainstream_cul.df, lb.NV_AGRICULTURE),
                                         (lb_mainstream_cul.df, lb.NV_POWER)],
                                        lb_mainstream_cul.df, lb.NV_TOTAL)
        if self.show_tributaries:
            df_utils.add_columns_across_dfs([(lb_mainstream_cul.df, lb.NV_TOTAL),
                                             (lb_tributary_cul.df, lb.NV_TRIBUTARY_CUL)],
                                            lb_mainstream_cul.df, lb.NV_TOTAL)

        # Arizona Mainstem
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.AZ_M_I_OTHER, lb.AZ_AGRICULTURE, lb.AZ_POWER], lb.AZ_MAINSTEM)
        df_utils.rename_column(lb_mainstream_cul.df, lb.AZ_WITHIN_SYSTEM, lb.AZ_CAP, inplace=True)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.AZ_CAP, lb.AZ_MAINSTEM], lb.AZ_COLORADO_RIVER_TOTAL)

        # Arizona Tributary
        if self.show_tributaries:
            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_LITTLE_COLORADO_CUL,
                                     lb.AZ_VIRGIN_CUL,
                                     lb.AZ_BILL_WILLIAMS_CUL,
                                     lb.AZ_TRIB_BELOW_LAKE_MEAD_CUL],
                                    lb.AZ_TRIBUTARY_CUL)
            df_utils.add_columns_across_dfs([
                (lb_mainstream_cul.df, lb.AZ_COLORADO_RIVER_TOTAL),
                (lb_tributary_cul.df, lb.AZ_GILA_CUL),
                (lb_tributary_cul.df, lb.AZ_TRIBUTARY_CUL)],
                lb_mainstream_cul.df, lb.AZ_TOTAL)

            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_VIRGIN_CUL,
                                     lb.NV_VIRGIN_CUL,
                                     lb.UT_VIRGIN_CUL],
                                    lb.VIRGIN_CUL)

            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_LITTLE_COLORADO_CUL,
                                     lb.NM_LITTLE_COLORADO_CUL],
                                    lb.LITTLE_COLORADO_CUL)

            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_GILA_CUL,
                                     lb.NM_GILA_CUL],
                                    lb.GILA_CUL)

            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.UT_VIRGIN_CUL,
                                     lb.UT_TRIB_ABOVE_LAKE_MEAD_CUL],
                                    lb.UT_TRIBUTARY_CUL)

            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.NM_GILA_CUL,
                                     lb.NM_LITTLE_COLORADO_CUL],
                                    lb.NM_TRIBUTARY_CUL)

            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_TRIBUTARY_CUL,
                                     lb.NV_TRIBUTARY_CUL,
                                     lb.UT_TRIBUTARY_CUL,
                                     lb.NM_TRIBUTARY_CUL],
                                    lb.LB_TRIBUTARY_CUL)
        else:
            df_utils.add_columns_across_dfs([
                (lb_mainstream_cul.df, lb.AZ_COLORADO_RIVER_TOTAL)],
                lb_mainstream_cul.df, lb.AZ_TOTAL)

        df_utils.copy_rows_by_year(df, lb_mainstream_cul.df)
        df_utils.copy_rows_by_year(df, lb_reservoirs_cul.df)
        if self.show_tributaries:
            df_utils.copy_rows_by_year(df, lb_tributary_cul.df)

        return df