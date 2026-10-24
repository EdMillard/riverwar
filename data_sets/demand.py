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
import pandas as pd
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils
from typing import Optional, List, Any, Tuple

from colorado.river_war import RiverWar


class Colors:
    """Shared color constants for demand charts."""
    CO = '#c050c0'
    UT = '#8080ff'
    WY = '#a0a0ff'
    NM = '#c0c0ff'

    CA1 = '#ef2828'
    CA2 = '#ff4040'
    CA3 = '#ff6060'
    CA4 = '#ff8080'

    NV1 = 'gray'
    NV2 = 'lightgray'

    AZ = '#cd5906'
    AZ1 = '#ef5926'
    AZ2 = '#ef6936'
    AZ3 = '#ef7946'
    AZ4 = '#ef8956'
    AZ5 = '#ef9966'
    AZ6 = '#efbb77'
    AZ7 = '#efdd99'

    UB = '#8080ff'
    EVAP = '#c5a67a'
    MX = 'darkgreen'


class Demand:
    def __init__(self, river_war:RiverWar):
        self.df_ub_cul: Optional[pd.DataFrame] = None
        self.df_lb_cul: Optional[pd.DataFrame] = None
        self.df_ub_users: Optional[pd.DataFrame] = None
        self.az_ltsc_data: Optional[pd.DataFrame] = None
        self.natural_flow_data: Optional[pd.DataFrame] = None

        self.totals: Optional[Tuple, List[Any]] = None
        self.lb_totals: Optional[Tuple, List[Any]] = None
        self.evap_totals: Optional[Tuple, List[Any]] = None
        self.trib_totals: Optional[Tuple, List[Any]] = None

        self.demand_series:List[Tuple] = self.build_data(river_war, show_tributaries=True)


    @staticmethod
    def build_demand_cul(df_ub_cul, df_lb_cul, ltsc_df, show_tributaries=False):
        series = [
            (df_ub_cul, ub.CO_WEST_SLOPE, Colors.CO),
            (df_ub_cul, ub.CU_UT, Colors.UT),
            (df_ub_cul, ub.CU_WY, Colors.WY),
            (df_ub_cul, ub.CU_NM, Colors.NM),
            (df_ub_cul, ub.UB_RESERVOIR_EVAP, all_b.EVAP_COLOR),
            (df_lb_cul, lb.MEXICO, lb.MX_COLOR),
            (df_lb_cul, lb.LB_RESERVOIR_EVAP, all_b.EVAP_COLOR),
            (df_lb_cul, lb.SALTON_INFLOW, all_b.EVAP_COLOR, {'hatch': '-', 'hatch_color': '#c040c0'}),
            (df_lb_cul, lb.IMPERIAL_VALLEY_CU, Colors.CA1, {'label': 'Imperial Valley'}),
            (df_lb_cul, lb.CA_OUTSIDE_SYSTEM, Colors.CA2, {'label': 'Metropolitan'}),
            (df_lb_cul, lb.CA_MAINSTEM, Colors.CA4),
            (df_lb_cul, lb.PALO_VERDE_CU, Colors.CA3, {'label': 'Palo Verde'}),
            (df_lb_cul, lb.NV_COLORADO_RIVER_TOTAL, Colors.NV2, {'label': 'NV'}),
            (df_lb_cul, lb.NV_TRIBUTARY_CUL, Colors.NV1, {'label': 'NV Trib'}),
            (ltsc_df, lb.AZ_LTSC_STORED, Colors.AZ7, {'label': 'CAP Aquifer Store', 'hatch': '|', 'hatch_color': '#ff8080'}),
            (df_lb_cul, lb.AZ_CAP, Colors.AZ6, {'label': 'CAP'}),
            (df_lb_cul, lb.AZ_CRIT_CU, Colors.AZ5, {'label': 'CRIT'}),
            (df_lb_cul, lb.WELLTON_MOHAWK_CU, Colors.AZ4, {'label': 'Wellton Mohawk'}),
            (df_lb_cul, lb.AZ_MAINSTEM, Colors.AZ3),
        ]
        if show_tributaries:
            series.append((df_lb_cul, lb.AZ_TRIBUTARY_CUL, Colors.AZ2, {'label': 'AZ Trib'}))
            series.append((df_lb_cul, lb.AZ_GILA_CUL, Colors.AZ1, {'label': 'AZ Gila'}))
            series.append((df_lb_cul, lb.UB_STATE_TRIB_IN_LB, 'darkblue'))
        return series

    def build_data(self, river_war, show_tributaries=False)->List:
        # ====================== UPPER BASIN ======================
        ub_cul = river_war.dataset.get('Upper Basin Cul')
        self.df_ub_cul = ub_cul.df

        ub_users = river_war.dataset.get('Upper Basin Users')
        self.df_ub_users = ub_users.df

        # ====================== LOWER BASIN ======================
        lb_cul = river_war.dataset.get('Lower Basin Cul')
        self.df_lb_cul = lb_cul.df

        # ====================== NATURAL FLOW ======================
        self.natural_flow_data = river_war.dataset.get('Natural Flow')

        # ====================== AZ Aquifer ======================
        self.az_ltsc_data = river_war.dataset.get('Az Ltsc')

        series = self.build_totals(show_tributaries)
        return series

    def build_totals(self, show_tributaries=False):
        # Final totals
        df_utils.add_columns_across_dfs([
            (self.df_ub_cul, ub.UB_RESERVOIR_EVAP),
            (self.df_lb_cul, lb.LB_RESERVOIR_EVAP),
            (self.df_lb_cul, lb.SALTON_INFLOW)],
            self.df_lb_cul, all_b.EVAP_TOTAL)

        df_utils.add_columns_across_dfs([
            (self.df_lb_cul, lb.CA_TOTAL),
            (self.df_lb_cul, lb.AZ_TOTAL),
            (self.df_lb_cul, lb.NV_TOTAL),
            (self.df_lb_cul, lb.LB_RESERVOIR_EVAP)],
            self.df_lb_cul, lb.LB_TOTAL)

        df_utils.add_columns_across_dfs([
            (self.df_ub_cul, ub.UB_TOTAL),
            (self.df_lb_cul, lb.LB_TOTAL),
            (self.df_lb_cul, lb.MEXICO)],
            self.df_lb_cul, all_b.DEMAND)

        df_utils.add_columns_across_dfs([
            (self.df_lb_cul, lb.UT_TRIBUTARY_CUL),
            (self.df_lb_cul, lb.NM_TRIBUTARY_CUL)],
            self.df_lb_cul, lb.UB_STATE_TRIB_IN_LB)

        df_utils.add_columns_across_dfs([
            (self.natural_flow_data.df, ub.NATURAL_LEES_FERRY)],
            self.natural_flow_data.df, all_b.SUPPLY)

        if show_tributaries:
            df_utils.add_columns_across_dfs([
                (self.df_lb_cul, lb.GILA_CUL)],
                self.natural_flow_data.df, all_b.SUPPLY)
            df_utils.moving_average(self.natural_flow_data.df, ub.SUPPLY, all_b.SUPPLY_3_YEAR_AVG, window=3)

        # ====================== DEMAND PIE CHART ======================
        self.totals = (0.0, 0.99, [
            ("Lower Basin", (self.df_lb_cul, lb.LB_TOTAL), 'maroon'),
            ("Upper Basin", (self.df_ub_cul, ub.UB_TOTAL), 'royalblue'),
            ("Mexico", (self.df_lb_cul, lb.MEXICO), Colors.MX),
            ("Demand", (self.df_lb_cul, all_b.DEMAND))
        ])

        self.lb_totals = (0.85, 0.99, [
            ("CA", (self.df_lb_cul, lb.CA_TOTAL), Colors.CA1),
            ("AZ", (self.df_lb_cul, lb.AZ_TOTAL), Colors.AZ),
            ("NV", (self.df_lb_cul, lb.NV_TOTAL), 'darkgray'),
            ("LB Evap", (self.df_lb_cul, lb.LB_RESERVOIR_EVAP), Colors.EVAP),
            ("LB Demand", (self.df_lb_cul, lb.LB_TOTAL), 'maroon')
        ])

        self.evap_totals = (0.0, 0.02, [
            ("UB Evap", (self.df_ub_cul, ub.UB_RESERVOIR_EVAP), Colors.EVAP),
            ("LB Evap", (self.df_lb_cul, lb.LB_RESERVOIR_EVAP), Colors.EVAP),
            ("Salton Evap", (self.df_lb_cul, lb.SALTON_INFLOW), Colors.EVAP),
            ("Total", (self.df_lb_cul, all_b.EVAP_TOTAL))
        ])

        self.trib_totals = (0.85, 0.07, [
            ("AZ Gila", (self.df_lb_cul, lb.AZ_GILA_CUL), Colors.AZ),
            ("AZ Trib", (self.df_lb_cul, lb.AZ_TRIBUTARY_CUL), Colors.AZ),
            ("NV Trib", (self.df_lb_cul, lb.NV_TRIBUTARY_CUL), 'darkgray'),
            ("UT Trib", (self.df_lb_cul, lb.UT_TRIBUTARY_CUL), Colors.UT),
            ("NM Trib", (self.df_lb_cul, lb.NM_TRIBUTARY_CUL), Colors.NM),
            ("Total", (self.df_lb_cul, lb.LB_TRIBUTARY_CUL))
        ])

        # AZ CAP/Aquifer LTSC
        ltsc_df = self.az_ltsc_data.df
        df_utils.subtract_columns_across_dfs(self.df_lb_cul, lb.AZ_MAINSTEM,
                                             [(self.df_lb_cul, lb.AZ_CRIT_CU),
                                              (self.df_lb_cul, lb.WELLTON_MOHAWK_CU)], result_column=lb.AZ_MAINSTEM)
        df_utils.subtract_columns_across_dfs(self.df_lb_cul, lb.AZ_CAP, [(ltsc_df, lb.AZ_LTSC_STORED)],
                                             result_column=lb.AZ_CAP)

        # CA Mainstem
        df_utils.subtract_columns_across_dfs(self.df_lb_cul, lb.CA_MAINSTEM, [(self.df_lb_cul, lb.PALO_VERDE_CU)],
                                             result_column=lb.CA_MAINSTEM)

        series = Demand.build_demand_cul(self.df_ub_cul, self.df_lb_cul, ltsc_df, show_tributaries=True)

        if show_tributaries:
            df_utils.add_columns_across_dfs([
                (self.df_lb_cul, lb.UB_STATE_TRIB_IN_LB),
                (self.df_lb_cul, lb.LB_TOTAL)
            ], self.df_lb_cul, 'LB Total with UB Tributaries')
        return series