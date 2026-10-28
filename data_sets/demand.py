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
    UT = '#6060ff'
    WY = '#A0A0ff'
    # NM = '#A0A0ff'
    NM = '#A0A0ff'

    CA = 'maroon'
    CA_SALTON = '#000000'
    CA_ALAMO = 'gray'
    CA_VOLCANO = 'darkgray'
    CA_IMPERIAL = '#800000'
    CA_MWD = '#a03030'
    CA_PALO_VERDE = '#c03030'
    CA_MAINSTEM = '#ff2020'

    CA1 = '#ef2828'
    CA2 = '#ff4040'
    CA3 = '#ff6060'
    CA4 = '#ff8080'

    NV1 = 'lightgray'
    NV2 = 'lightgray'

    AZ = '#ef5926'
    AZ1 = '#ff8866'
    AZ2 = '#ffaa88'
    AZ3 = '#ef7946'
    AZ4 = '#ef8956'
    AZ5 = '#ef9966'
    AZ6 = '#efbb77'
    AZ7 = '#efdd99'

    MX = 'darkgreen'
    MX_CIENEGA = 'cyan'
    MX_DELTA = 'lightblue'

    LB = 'maroon'
    UB = '#8080ff'

    NATURAL_FLOW = "cornflowerblue"

    EVAP = '#c5a67a'

    Wet = "green"
    Drought = "red"
    Monsoon = "black"

class Demand:
    monsoon_years = [
        (1911, Colors.Monsoon, "SW Colorado Flood of the century"),
        (2005, Colors.Monsoon, "Monsoon"),
        (2006, Colors.Monsoon, "Monsoon"),
        (2013, Colors.Monsoon, "Monsoon"),
        (2014, Colors.Monsoon, "Monsoon"),
        (2017, Colors.Monsoon, "Monsoon"),
        (2022, Colors.Monsoon, "Monsoon"),
        (2026, Colors.Monsoon, "SW Colorado Flood of the century"),
    ]
    wet_v_dry_years = [

        (1906, Colors.Wet, "Wet"),
        (1907, Colors.Wet, "Wet"),
        (1909, Colors.Wet, "Wet"),
        (1912, Colors.Wet, "Wet"),
        (1914, Colors.Wet, "Wet"),
        (1916, Colors.Wet, "Wet"),
        (1917, Colors.Wet, "Wet"),
        (1920, Colors.Wet, "Wet"),
        (1921, Colors.Wet, "Wet"),
        (1922, Colors.Wet, "Wet"),
        (1923, Colors.Wet, "Wet"),
        (1927, Colors.Wet, "Wet"),
        (1929, Colors.Wet, "Wet"),

        # 1930s
        (1931, Colors.Drought, "Drought"),
        (1932, Colors.Wet, "Wet"),
        (1934, Colors.Drought, "Severe Drought"),
        (1938, Colors.Wet, "Wet"),
        (1940, Colors.Drought, "Drought"),

        # 1940's
        (1941, Colors.Wet, "Wet"),
        (1942, Colors.Wet, "Wet"),

        # mid-century
        (1952, Colors.Wet, "Wet"),
        (1953, Colors.Drought, "Drought"),
        (1954, Colors.Drought, "Drought"),
        (1955, Colors.Drought, "Drought"),
        (1956, Colors.Drought, "Drought"),
        (1957, Colors.Wet, "Wet"),
        (1959, Colors.Drought, "Drought"),
        (1961, Colors.Drought, "Drought"),
        (1962, Colors.Wet, "Wet"),
        (1963, Colors.Drought, "Drought"),
        (1965, Colors.Wet, "Wet"),

        # 1970s
        (1973, Colors.Wet, "Wet"),
        (1977, Colors.Drought, "Severe Drought"),
        (1979, Colors.Wet, "Wet"),

        # 1980s wet
        (1981, Colors.Drought, "Drought"),
        (1983, Colors.Wet, "Wet"),
        (1984, Colors.Wet, "Wet"),
        (1985, Colors.Wet, "Wet"),
        (1986, Colors.Wet, "Wet"),

        # late 80s / 90s
        (1989, Colors.Drought, "Drought"),
        (1990, Colors.Drought, "Drought"),
        (1993, Colors.Wet, "Wet"),
        (1995, Colors.Wet, "Wet"),
        (1997, Colors.Wet, "Wet"),

        # 2000s
        (2000, Colors.Drought, "Millennial Drought Started"),
        (2001, Colors.Drought, "Drought"),
        (2002, Colors.Drought, "Severe Drought"),
        (2003, Colors.Drought, "Drought"),
        (2004, Colors.Drought, "Drought"),

        # 2010s
        (2011, Colors.Wet, "Wet"),
        (2012, Colors.Drought, "Severe Drought"),
        (2013, Colors.Drought, "Drought"),
        (2018, Colors.Drought, "Drought"),
        (2019, Colors.Wet, "Wet"),

        # 2020s
        (2020, Colors.Drought, "Drought"),
        (2021, Colors.Drought, "Severe Drought"),
        (2022, Colors.Drought, "Drought"),
        (2023, Colors.Wet, "Wet"),
    ]

    def __init__(self, river_war:RiverWar, show_tributaries: bool = False):
        self.df_ub_cul: Optional[pd.DataFrame] = None
        self.df_lb_cul: Optional[pd.DataFrame] = None
        self.df_ub_users: Optional[pd.DataFrame] = None
        self.az_ltsc_data: Optional[pd.DataFrame] = None
        self.natural_flow_data: Optional[pd.DataFrame] = None

        self.totals: Optional[Tuple, List[Any]] = None
        self.lb_totals: Optional[Tuple, List[Any]] = None
        self.evap_totals: Optional[Tuple, List[Any]] = None
        self.trib_totals: Optional[Tuple, List[Any]] = None

        self.demand_series:List[Tuple] = self.build_data(river_war, show_tributaries=show_tributaries)


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