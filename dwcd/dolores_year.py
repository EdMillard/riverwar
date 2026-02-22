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
import numpy as np
import json
from pathlib import Path

from api.ui_abstraction import UIAbstraction
from dwcd.water_year import WaterYear
from api.event_log import EventLog
from source.water_year_info import WaterYearInfo
from api.pool import PoolQueue, DrainRun, DrainType, FillRun, FillType
from dwcd.mvi_pools import NarrInMcpheePool, TottenExchangePool, CallWaterPool, UpstreamExchangePool, MVIProjPool

# 2003-2009   'NAR CALL'
# 2010-       'NARR FILL'
#
# 2019-       'CUM NARR IN MCPHEE'

# 2003-       'U/S USERS EXCH'

# 2003-       'MVI PROJ'

# 1986-2002   'MVI CALL' simple pool, 'MVI DAILY' daily call water cfs...sometimes, sometimes no column at all
# 2003-2004   'MVI CALL + TO(T) EX' MVI CALL, TO EX and US EX were stored in one pool, MVI PROJ pool was added
# 2005        'MVI PROJ & TO EX &' were moved to MVI PROJ pool
# 2006-2022   'TO EX & U/S EX' are combined in their own pool
# 2023-       'TO EX' 'U/S EX' each have their own pool

# 2009        chaos, maybe lawsuit between MVI and DWCD, MVI PROJ was daily drain, not a pool for this one year
# 2010-       'MVI CALL STOR', 'MVI CALL SPILLED OR USED', 'MVI APR-JUNE (DIV+ CALL)' appeared, maybe from lawsuit

# 1986-2003   'MVI,CTZ' sometimes has MWC in it, since it's also lumped in here
# 2003-2010   'MWC', 'CTZ', 'CTZ & UTE' also 'CTX & UTE'
# 2011-       'MWC NON - PROJ', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ'

# 1986-1989   No fish pool, just 'BELOW MC  PHEE'
# 1990        'FISH LOAN'
# 1991-2003   'REMAIN RELEASE'
# 2004-       'FISH LEFT'
#
# 1986-2003   'BELOW MC  PHEE'
# 2004        'BELOW MCPHEE'
# 2005-       'BELOW MCP'
#
# 2008-       'SPILL'

# 2003        'MVI CALL EVAP acft'
# 2004-       'MVI STORED EVAP'
#
# 2017-       'PAN EVAP'
#
# 2021-       'DWR EST PAN EVAP'

# 2009-       'DIST. CLASS "B"'

# 2008-2009   'UTES FROM MVIC'
# 2010-2014   'UTES FROM DWCD'
# 2015-       'UF&R LEASE WATER'

# 2005-        TOTTEN FRESH WATER

class DoloresYear(WaterYear):
    patch_cum_narr_in_mcphee_2025_1 = True
    patch_cum_narr_in_mcphee_2025_2 = True
    patch_mvi_use_1 = True
    patch_mvi_highline_2025_1 = True
    patch_cortez_non_proj_2025_1 = True

    patch_to_ex_2024_1 = True

    depends = {
        'RESERV TOT CAP': ['RESERV ELEV'],
        'AC  FT CHANGE': ['RESERV TOT CAP'],
        'ACTIVE CAP': ['RESERV TOT CAP'],
        'CONV  TO CFS': ['AC  FT CHANGE'],
        'CALC INF/OTF': ['DOLORES RIVER','CONV  TO CFS', 'RECORD INFLOW', 'RECORD OTF', 'NARR FILL'],
        'CALC INFLOW': ['CALC INF/OTF'],
        'RECORD INFLOW': ['DOLORES RIVER', 'LOST CAN'],
        'TOTAL INFLOW': ['RECORD INFLOW', 'CALC INFLOW'],
        'F-BAY BAL': ['DOLORES TUNNEL', 'MWC', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ'],
        'MVI HIGHLINE': ['DOLORES TUNNEL', 'WET LAND', 'UTE F&R', 'SEELEY QUEST', 'MWC', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ', 'F-BAY BAL'],
        'MVI TOTAL WATER USED': ['MVI HIGHLINE', 'LONE PINE', 'U LAT', 'TOTTEN (FRESH WATER)', 'DIST CLASS B', 'NARR FILL'],
        'MVI TOTAL IRRIG': ['MVI TOTAL WATER USED', 'MVI STOCK'],
        'MVI CALL STOR': ['DOLORES RIVER', 'RECORD INFLOW', 'MVI TOTAL WATER USED', 'UF&R LEASE WATER', 'U/S USERS EXCH', 'D/S SENIOR MVIC', 'SPILL', 'TO EX'],
        'MVI CALL SPILLED OR USED': [], # FIXME
        'MVI APR- JUNE (DIV+ CALL)': [], # FIXME
        'TO EX': ['MVI STORABLE', 'CUM NARR IN MCPHEE', 'MVI STORED EVAP'],
        'MVI PROJ': ['MVI STORABLE', 'U/S EX'],
        'SPILL': ['BELOW MCP'],
        'FISH LEFT': ['BELOW MCP', 'SPILL'],
        'RECORD OTF': ['WET LAND', 'UTE F&R', 'SEELEY QUEST','MWC', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ', 'F-BAY BAL', 'MVI TOTAL WATER USED', 'DV  CR CANAL', 'BELOW MCP'],
        'CALC OTF': ['CALC INF/OTF'],
        'TOTAL OTF': ['RECORD OTF', 'CALC OTF'],
        'NARR FILL': ['LONE PINE'],
        'NARR FILL IN MCPHEE': [], # FIXME
        'MCPHEE DAILY EVAP IN': ['DWR EST PAN EVAP'],
        'LAKE SURFACE AREA': [], # FIXME
        'MCPHEE DAILY EVAP AF': ['RESERV ELEV', 'MCPHEE DAILY EVAP IN', 'LAKE SURFACE AREA'],
        'NARR IN MCP EVAP': ['MCPHEE DAILY EVAP AF', 'CUM NARR IN MCPHEE', 'ACTIVE CAP'],
        'CUM NARR IN MCP EVAP': ['NARR IN MCP EVAP'],
        'CUM NARR IN MCPHEE': [], # FIXME
        'MVI STOCK': [], # FIXME
        'MVI STORABLE': [], # FIXME
        'MVI STORED EVAP': [], #FIXME
        'DIST CLASS B': [], # No dependencies, all formulas
        'U/S USERS EXCH': ['GRNDHOG DISCHARGE'],
        'UF&R LEASE WATER': ['UTE F&R'],
        'TOTAL TUNNEL Misc.': ['WET LAND', 'SEELEY QUEST', 'F-BAY BAL'],
        'LAKE EVAP': ['PAN EVAP'],
        'LAKE EVAP VOL': ['LAKE EVAP', 'LAKE SURFACE AREA'],
        'DWCD 505 FLOWS AVAIL': [], # FIXME
        'DWCD 505 CFS DIRECT DIV': ['DWCD 505 FLOWS AVAIL', 'UTE F&R', 'DV  CR CANAL', 'MVIC DAILY POOL USED']
    }

    def __init__(self, ui_abstraction):
        super().__init__(ui_abstraction)

        self.event_log:EventLog = EventLog()

    def run(self):
        if self.water_year_info.year != 2025:
            DoloresYear.patch_cum_narr_in_mcphee_2025_1 = False
            DoloresYear.patch_cum_narr_in_mcphee_2025_2 = False
            DoloresYear.patch_mvi_use_1 = False
            DoloresYear.patch_mvi_highline_2025_1 = True
            DoloresYear.patch_cortez_non_proj_2025_1 = False
        if self.water_year_info.year != 2024:
            DoloresYear.patch_to_ex_2024_1 = False

        self.config['logger'] = self.logger
        self.calc = self.calc_water_year(self.water_year_info, self.logger, self.n, self.inputs_dwcd, self.inputs_cdss, self.config)

        with self.file_names['units_json'].open("w") as file:
            json.dump(self.units, file, indent=4)

        self.sources = {
            "exl": self.n,
            "out": self.calc,
            "in": self.inputs_dwcd,
        }
        if self.custom_data:
            self.sources['custom'] = self.custom_data
        if self.load_cdss_data:
            self.sources['cdss'] = self.inputs_cdss
        if self.load_usgs_data:
            self.sources['usgs'] = self.inputs_usgs
        if self.load_usbr_data:
            self.sources['usbr'] = self.inputs_usbr

    def auto_config_custom_data(self):
        user_configs = {}
        self.config['user'] = user_configs

        dates = self.y['DATE']

        # Flow runs

        if self.water_year_info.year >= 2008:
            spill_default_equations = [
                '=x[\'BELOW MCP\'][day]',
            ]
            WaterYear.build_flow_runs('SPILL', user_configs, self.custom_data, self.equations,
                                             self.y, dates, default_equations=spill_default_equations)

        if self.water_year_info.year >= 2003:
            mcphee_evap_default_equations = [
                '=x[\'DWR EST PAN EVAP\'][day]*0.7',
                #'=x[\'DWR EST PAN EVAP\'][day]',
            ]
            WaterYear.build_flow_runs('MCPHEE DAILY EVAP IN', user_configs, self.custom_data, self.equations,
                                             self.y, dates, default_equations=mcphee_evap_default_equations)

        narr_fill_default_equations = [
            '=x[\'LONE PINE\'][day]',
            '=IF(x[\'LONE PINE\'][day]="","",x[\'LONE PINE\'][day])',
            '=IF(x[\'LONE PINE\'][day]=0,"0",x[\'LONE PINE\'][day])',
            '=IF(x[\'LONE PINE\'][day]=0,"",x[\'LONE PINE\'][day])',
        ]
        WaterYear.build_flow_runs('NARR FILL', user_configs, self.custom_data, self.equations, self.y, dates,
                                         default_equations=narr_fill_default_equations)

        WaterYear.build_flow_runs('F-BAY BAL', user_configs, self.custom_data, self.equations, self.y, dates)

        WaterYear.build_flow_runs('MVI STOCK', user_configs, self.custom_data, self.equations,self.y, dates)
        WaterYear.build_mvi_stock_run_detail('MVI STOCK', user_configs, self.equations, dates)
        # has_custom_data = WaterYear.build_custom_data('MVI STOCK', self.equations, self.y, self.custom_data, ['1.04', '1.06'])

        WaterYear.build_flow_runs('UF&R LEASE WATER', user_configs, self.custom_data, self.equations, self.y, dates)
        if self.water_year_info.year >= 2019:
            WaterYear.build_flow_runs('NARR FILL IN MCPHEE', user_configs, self.custom_data, self.equations, self.y, dates)

        if self.water_year_info.year >= 2002:
            WaterYear.build_flow_runs('DIST CLASS B', user_configs, self.custom_data, self.equations, self.y, dates)

        # runs = WaterYear.build_flow_runs('U/S USERS EXCH', user_configs, self.custom_data, self.equations, self.y, dates)
        if self.water_year_info.year >= 2003:
            # From 2003-2013 this is just an input channel with tech entering values to fill the pool target
            # This currently only works when 'GRNDHOG DISCHARGE' comes available in 2014 to cap 'U/S USERS EXCH'
            ground_hog_discharges = self.y.get('GRNDHOG DISCHARGE')
            WaterYear.build_upstream_exchange_fill_detail('U/S USERS EXCH', user_configs, self.equations, self.y, dates,
                                                          ground_hog_discharges)

        WaterYear.build_custom_data('MWC', self.equations, self.y, self.custom_data, ['1.02'])
        WaterYear.build_custom_data('CORTEZ PROJ', self.equations, self.y, self.custom_data, ['1.04', 'UTE PROJ'])
        WaterYear.build_custom_data('CORTEZ NON - PROJ', self.equations, self.y, self.custom_data, ['1.04', 'UTE PROJ'])
        WaterYear.build_custom_data('UTE PROJ', self.equations, self.y, self.custom_data, ['1.04', '1.06'])
        WaterYear.build_custom_data('UTE F&R', self.equations, self.y, self.custom_data, ['1.05'])
        WaterYear.build_custom_data('RECORD INFLOW', self.equations, self.y, self.custom_data, ['DOLORES RIVER'])

    def analyze(self, exl, out, inp):
        user_configs = self.config['user']

        dates = self.y['DATE']

        # MVI Pool fill, drain, evap runs
        evap_variable_names = ['NARR IN MCP EVAP', 'MVI STORED EVAP']
        fill_drain_variable_names = ['MVI STORABLE', 'RECORD INFLOW']

        fill_values = drain_values = DoloresYear.calc_mvi_storable(exl, inp, dates, self.water_year_info)
        if 'SPILL' in  self.y:
            spill_values = self.y['SPILL']
        else:
            spill_values = None

        self.fill_runs['NARR FILL'] = self.analyze_narr(self.logger, self.config, exl, dates,
                                                        fill_values, drain_values, spill_values)

        if self.water_year_info.year >= 2008:
            spills = WaterYear.get_flow_runs(self.config, self.logger, 'SPILL')
            if spills is not None:
                spill_runs = PoolQueue([])
                for spill in spills:
                    start_day = WaterYearInfo.day_for_date(dates, spill[0])
                    end_day = WaterYearInfo.day_for_date(dates, spill[1])
                    spill_run = DrainRun('SPILL', DrainType.SPILL, start_day, dates)
                    spill_run.end_day = end_day
                    spill_runs.append(spill_run)
                self.drain_runs['SPILL'] = spill_runs

        mvi_evap = None
        if 'MVI STORED EVAP' in self.y:
            if 'NARR IN MCP EVAP' in self.y:
                apr1 = WaterYear.day_for_date(dates, 'Apr-1')
                mvi_evap = self.y['MVI STORED EVAP'].copy()
                mvi_evap[:apr1] = self.y['NARR IN MCP EVAP'][:apr1]
                out['MVI EVAP'] = mvi_evap
            else:
                out['MVI EVAP'] = mvi_evap = self.y['MVI STORED EVAP'].copy()

        if 2005 <= self.water_year_info.year < 2006:
            mvi_call_var_name = 'MVI CALL STOR'
        elif 2003 <= self.water_year_info.year < 2005:
            mvi_call_var_name = 'MVI CALL TO EX U/S EX'
        elif self.water_year_info.year < 2003:
            mvi_call_var_name = 'MVI CALL STOR'
        else:
            mvi_call_var_name = 'MVI CALL STOR'
        self.build_pool_queue_var(mvi_call_var_name, fill_values, drain_values, spill_values, user_configs,
                              fill_drain_variable_names, evap_variable_names, mvi_evap, dates, fill_max_end_date='Jun-30')
        if 2003 <= self.water_year_info.year <= 2004:
            if self.water_year_info.year == 2003:
                to_ex_paper_fill = FillRun('MVI CALL TO EX U/S EX', FillType.PAPER_FILL, WaterYear.day_for_date(dates, 'Jun-1'), dates)
                to_ex_paper_fill.paper_fill =  3400.0 / WaterYear.af_to_cfs

                fill_runs = self.fill_runs.get('MVI CALL TO EX U/S EX')
                if fill_runs:
                    mvi_call_store_run = fill_runs[0]
                    self.config['day_totten_exchange_fill_ends'] = mvi_call_store_run.start_day
                    fill_runs.append(to_ex_paper_fill)
                    self.fill_runs['MVI CALL TO EX U/S EX'] = fill_runs
                else:
                    self.fill_runs['MVI CALL TO EX U/S EX'] = [to_ex_paper_fill]

            else:
                fill_runs = self.fill_runs['MVI CALL TO EX U/S EX']
                if fill_runs:
                    mvi_call_store_run = fill_runs[0]
                    fill_run =mvi_call_store_run.copy()
                    fill_run.variable_name = 'TO EX'
                    fill_run.target = self.config.get('TO EX')
                    if fill_run.target is None:
                        fill_run.target = 3400.0 / WaterYear.af_to_cfs
                    storable = exl.get('MVI STORABLE')
                    if storable is not None:
                        pool = WaterYear.get_out('TO EX', out, len(storable))
                        fill_run.fill_pool(pool, storable)
                        out['MVI CALL TO EX U/S EX'] = pool.copy()
                        self.config['day_totten_exchange_fill_ends'] = fill_run.complete_day
                    pass

        # Totten and Upstream Exchange
        #
        if self.water_year_info.year >= 2003:
            if self.water_year_info.year >= 2023:
                to_ex_var_name = 'TO EX'
            else:
                to_ex_var_name = 'TO EX & U/S EX'
            if to_ex_var_name in exl:
                self.build_pool_queue_var(to_ex_var_name, fill_values, drain_values, spill_values, user_configs,
                                          fill_drain_variable_names, evap_variable_names, mvi_evap, dates)

            if 'U/S USERS EXCH' in exl:
                us_exch_values = self.y['U/S USERS EXCH']
                self.build_pool_queue_var('U/S EX', us_exch_values, drain_values, spill_values, user_configs,
                                      fill_drain_variable_names, evap_variable_names, mvi_evap, dates)
                if 'U/S EX' in self.fill_runs:
                    fill_queue: PoolQueue = PoolQueue([])
                    fill_run:FillRun|None = None
                    end_day = 0
                    end_date = ''
                    mvi_upstream_exchange_runs = WaterYear.get_flow_runs(self.config, self.logger, 'U/S USERS EXCH')
                    for run in mvi_upstream_exchange_runs:
                        start_date = run[0]
                        start_day = WaterYear.day_for_date(dates, start_date)
                        if end_day and start_day != end_day+1:
                            # Multiple fill runs with a gap between them
                            if fill_run:
                                fill_run.append_date_value(end_date, 0)
                        end_date = run[1]
                        end_day = WaterYear.day_for_date(dates,end_date)
                        value = run[2]
                        if not fill_run:
                            fill_run = FillRun('U/S EX', FillType.PAPER_FILL, start_day, dates)
                        fill_run.append_date_value(start_date, value)
                    if fill_run:
                        fill_run.end_day = end_day+1
                        fill_queue.append(fill_run)
                    self.fill_runs['U/S EX'] = fill_queue

        # Project Pool
        #
        if self.water_year_info.year == 2009:
            # 'MVI PROJ' is broken in 2009, its daily drain from the pool, not how much water is in the pool
            WaterYear.build_flow_runs('MVI PROJ', user_configs, self.custom_data, self.equations, self.y, dates)
        else:
            if 2005 <= self.water_year_info.year <= 2006:
                mvi_proj_var_name = 'MVI PROJ TO EX U/S EX'
            else:
                mvi_proj_var_name = 'MVI PROJ'
            if mvi_proj_var_name in exl:
                self.build_pool_queue_var(mvi_proj_var_name, fill_values, drain_values, spill_values, user_configs,
                                          fill_drain_variable_names, evap_variable_names, mvi_evap, dates,
                                          do_paper_drains=True)

        # Narr Fill In McPhee
        #
        if self.water_year_info.year >= 2019:
            if self.water_year_info.year == 2024:
                transfer_to_names = [
                    "-x['NARR FILL']",
                ]
            else:
                transfer_to_names = []
            cum_narr_fill_drain_variable_names = [
                'NARR FILL IN MCPHEE',  # This is used before Apr-1
                'RECORD INFLOW'         # This is used after Apr-1
            ]
            # narr_fill_values = self.y['NARR FILL IN MCPHEE']
            self.build_pool_queue_var('CUM NARR IN MCPHEE', fill_values, drain_values, spill_values, user_configs,
                                      cum_narr_fill_drain_variable_names, evap_variable_names, mvi_evap, dates,
                                      allow_transfers=True, transfer_to_names=transfer_to_names, do_paper_drains=True)

        self.fill_queue = PoolQueue.build_pool_queue(self.logger, self.fill_runs, 'Fill')
        self.drain_queue = PoolQueue.build_pool_queue(self.logger, self.drain_runs, 'Drain')
        self.evap_queue = PoolQueue.build_pool_queue(self.logger, self.evap_runs, 'Evap')

    def analyze_narr(self, logger, config, exl, dates, fill_values, drain_values, spill_values):
        narr_fill_runs = []
        if 'NARR CALL' in exl:
            # 2003-2009
            user_configs = self.config['user']
            fill_drain_variable_names = ['MVI STORABLE', 'RECORD INFLOW']
            self.build_pool_queue_var('NARR CALL', fill_values, drain_values, spill_values, user_configs,
                                      fill_drain_variable_names, [], None, dates)

        if 'NARR FILL' in exl:
            # 2010-
            narr_fills = WaterYear.get_flow_runs(config, logger, 'NARR FILL')
            if narr_fills is not None:
                narr_fill_runs = PoolQueue([])
                for narr_fill in narr_fills:
                    start_day = WaterYearInfo.day_for_date(dates, narr_fill[0])
                    end_day = WaterYearInfo.day_for_date(dates, narr_fill[1])
                    narr_fill_run = FillRun('NARR FILL', FillType.FILL, start_day, dates)
                    narr_fill_run.end_day = end_day
                    narr_fill_runs.append(narr_fill_run)
        return narr_fill_runs

    def calc_water_year(self, water_year_info:WaterYearInfo, logger, exl, inp, inp_cdss, config):
        self.event_log.start_log()

        water_year = water_year_info.year
        print("Run Water Year", water_year)

        out = {}

        # Automatically generate config from Excel, if Python is standalone(without Excel) user has to do this config
        self.analyze(exl, out, inp)

        ute_farms_loss_adj = 1.05
        config['upstream_user_exchange_af'] = 1641

        out['DATE'] = dates = exl['DATE']

        WaterYear.pre_process(logger, exl, inp, dates)

        apr1 =  WaterYear.day_for_date(dates, 'Apr-1')

        if 'TOWAOC' in inp_cdss and inp_cdss['TOWAOC'] is not None:
            out['UTE F&R'] = inp_cdss['TOWAOC']['val'] * ute_farms_loss_adj

        # McPhee Reservoir
        #
        reserve_tot_cap_oct31 = WaterYear.get_config(config, 'oct31', 'RESERV TOT CAP')
        out['RESERV TOT CAP'] = WaterYear.get_capacities(inp['RESERV ELEV'], self.mcphee_elevation_to_capacity, fallback_capacity=None)
        num_days = len(inp['RESERV ELEV'])

        out['LAKE SURFACE AREA'] = WaterYear.get_surface_areas(inp['RESERV ELEV'], self.mcphee_elevation_to_surface_area, fallback_area=None)
        # Interpolated has bugs
        # out['LAKE SURFACE AREA'] = WaterYear.get_surface_area_interpolated(inp['RESERV ELEV'], self.mcphee_elevation_to_surface_area, fallback_area=None)

        out['AC  FT CHANGE'] = WaterYear.compute_int_diffs(logger, 'RESERV TOT CAP', out['RESERV TOT CAP'], reserve_tot_cap_oct31) # FIXME 2024 oct 31 value
        out['ACTIVE CAP'] = out['RESERV TOT CAP'] - WaterYear.mcphee_dead_pool_af
        out['CONV  TO CFS'] = out['AC  FT CHANGE'] / WaterYear.af_to_cfs

        out['RECORD INFLOW'] = inp['DOLORES RIVER'] + inp['LOST CAN']
        WaterYear.apply_custom_data(self.custom_data, 'RECORD INFLOW', out['RECORD INFLOW']) # 2002 has this

        # Tunnel
        #
        DoloresYear.calc_tunnel_flows(inp, out, dates, self.custom_data, water_year_info)
        out['DOMESTIC'] = exl['MWC'] + exl['CORTEZ NON - PROJ'] + exl['CORTEZ PROJ'] + out['UTE PROJ']
        self.units['DOMESTIC'] = 'CFS'

        out['F-BAY BAL'] = WaterYear.output(num_days)
        forebay_runs = WaterYear.get_flow_runs(config, logger, 'F-BAY BAL')
        if forebay_runs is not None:
            for forebay_run in forebay_runs:
                if forebay_run[0] is None or not isinstance(forebay_run[0], str):
                    day_begins = 0
                else:
                    day_begins = WaterYear.day_for_date(dates, forebay_run[0])
                if forebay_run[1] is None or not isinstance(forebay_run[1], str):
                    day_ends = num_days - 1
                else:
                    day_ends = WaterYear.day_for_date(dates, forebay_run[1])
                out['F-BAY BAL'][day_begins:day_ends+1] = inp['DOLORES TUNNEL'][day_begins:day_ends+1] - out['DOMESTIC'][day_begins:day_ends+1]
        out['DOMESTIC'] = out['DOMESTIC'] + out['F-BAY BAL']

        out['GATE 504'] = inp['WET LAND'] + inp['SEELEY QUEST']  # FIXME Totten Fresh Water is here too?
        self.units['GATE 504'] = 'CFS'
        out['TOTAL TUNNEL Misc.'] = out['GATE 504'] + out['DOMESTIC']

        # Finish Inflow/Outflow
        #
        out['RECORD OTF'] = inp['DOLORES TUNNEL'] + inp['LONE PINE'] + inp['U LAT'] + inp['DV  CR CANAL'] + inp['BELOW MCP']
        if water_year_info.year == 2024:
            # FIXME - Hack to get 2024 RECORD OTF to balance
            out['RECORD OTF'][0:apr1-15] = out['RECORD OTF'][0:apr1-15] - exl['NARR FILL'][0:apr1-15]
        elif water_year_info.year == 2023:
            # FIXME - Hack to get 2023 RECORD OTF to balance
            out['RECORD OTF'][0:apr1+3] = out['RECORD OTF'][0:apr1+3] - exl['NARR FILL'][0:apr1+3]
            out['RECORD OTF'][0:apr1+10] = out['RECORD OTF'][0:apr1+10] + exl['UTE F&R'][0:apr1+10]

            fbay = WaterYear.output(num_days)
            oct31 = WaterYear.day_for_date(dates, 'Oct-31')
            fbay[apr1:oct31+1] = inp['DOLORES TUNNEL'][apr1:oct31+1] - (exl['MWC'][apr1:oct31+1]
                                                + exl['CORTEZ NON - PROJ'][apr1:oct31+1] + exl['UTE PROJ'][apr1:oct31+1])
            out['RECORD OTF'][apr1:apr1+10] = out['RECORD OTF'][apr1:apr1+10] - fbay[apr1:apr1+10]

            oct14 = WaterYear.day_for_date(dates, 'Oct-14')
            fbay[oct14:oct31+1] =  fbay[oct14:oct31+1] - exl['UTE F&R'][oct14:oct31+1]
            out['RECORD OTF'][oct14:oct31+1] = out['RECORD OTF'][oct14:oct31+1] - fbay[oct14:oct31+1]

        out['CALC INF/OTF'] = out['CONV  TO CFS'] - (out['RECORD INFLOW'] - out['RECORD OTF'])
        if water_year_info.year == 2024:
            # Not clear why these two days are the only ones that break because of the NARR transfers
            jun9 = WaterYear.day_for_date(dates, 'Jun-09')
            jun11 = jun9 + 2
            out['CALC INF/OTF'][jun9:jun11] = out['CALC INF/OTF'][jun9:jun11] + exl['NARR FILL'][jun9:jun11]
        out['CALC OTF'] = WaterYear.negative_as_positive(out['CALC INF/OTF'])
        out['TOTAL OTF'] = out['RECORD OTF'] + out['CALC OTF']
        out['CALC INFLOW'] = WaterYear.positive_values(out['CALC INF/OTF'])
        out['TOTAL INFLOW'] = out['RECORD INFLOW'] + out['CALC INFLOW']

        # McPhee evap
        #
        out['MCPHEE DAILY EVAP IN'] = inp['DWR EST PAN EVAP'] * 0.7
        if water_year_info.year == 2024:
            # DWCD has empty cells for these days, so zero, custom data doesn't currently pick up empty cells
            jan29 = WaterYear.day_for_date(dates, 'Jan-29')
            jan31 = WaterYear.day_for_date(dates, 'Jan-31')
            out['MCPHEE DAILY EVAP IN'][jan29:jan31+1] = 0
        WaterYear.apply_custom_data(self.custom_data, 'MCPHEE DAILY EVAP IN', out['MCPHEE DAILY EVAP IN'])

        out['MCPHEE DAILY EVAP AF'] = out['MCPHEE DAILY EVAP IN'] / 12 * out['LAKE SURFACE AREA']
        # FIXME Probably should consolidate these duplicate variables
        out['LAKE EVAP'] = inp['PAN EVAP'] * 0.7
        out['LAKE EVAP VOL'] = out['LAKE EVAP'] / 12 * out['LAKE SURFACE AREA']

        out['SPILL'] = DoloresYear.run_spill_runs(config, logger, exl, out, self.custom_data, dates)

        # Fish pool
        #
        if water_year_info.year >= 1990:
            out['FISH LEFT'] = DoloresYear.calc_fish_pool_left(config, exl, inp, dates, water_year_info)

        # DWCD 505 Water Right
        #
        DoloresYear.calc_dwcd(out, exl, inp, dates)

        # MVI Ute Lease Water
        #
        DoloresYear.calc_mvi_class_a_lease(config, logger, out, inp, dates)

        # MVI Class B water
        #
        if water_year_info.year == 2025:
            # Manually configured
            DoloresYear.mvi_dist_class_b(config, logger, out, dates, water_year_info)
        else:
            # Auto configured using custom data
            out['DIST CLASS B'] = WaterYear.output(num_days)
            WaterYear.apply_custom_data(self.custom_data, 'DIST CLASS B', out['DIST CLASS B'])

        pool_queue = self.get_pool_runs_all()
        storable = DoloresYear.calc_mvi_storable(exl, inp, dates, water_year_info)

        if water_year_info.year >= 2019:
            narr_fill_in_mcphee_runs = WaterYear.get_flow_runs(config, logger, 'NARR FILL IN MCPHEE')
            self.pools['CUM NARR IN MCPHEE'] = NarrInMcpheePool('CUM NARR IN MCPHEE', 'MVIC', exl, inp, out, dates,
                                                                 water_year_info, pool_queue, narr_fill_in_mcphee_runs,
                                                                 self.custom_data, storable)

        if water_year_info.year >= 2003:
            self.pools['TO EX'] = TottenExchangePool('TO EX', 'MVIC', config, exl, out, dates, water_year_info,
                                                      pool_queue, storable)

        self.pools['MVI CALL STOR'] = CallWaterPool('MVI CALL STOR', 'MVIC', exl, out, dates, pool_queue)

        if water_year_info.year >= 2003:
            self.pools['U/S EX'] = UpstreamExchangePool('U/S EX', 'MVIC', config, exl, inp, out, dates,
                                                         water_year_info, pool_queue)
            self.pools['MVI PROJ'] = MVIProjPool('MVI PROJ', 'MVIC', exl, out, dates, pool_queue)

        # Narraguinnep fill from Lone Pine mostly off season, transfers from NARR IN MCPHEE to Narraguinnep
        #
        narr_fill = DoloresYear.calc_narr_fill(exl, inp, out, self.custom_data, dates, pool_queue)

        # MVI Usage
        #
        DoloresYear.calc_mvi_use(config, logger, exl, inp, out, self.custom_data, dates, water_year_info, self.units,
                                 narr_fill)

        # MVI Pool Filling
        #
        oct31 = WaterYear.day_for_date(dates, 'Oct-31')
        for day in range(0, oct31):
            date_str = WaterYearInfo.format_to_month_day(dates[day])
            if date_str == 'Mar-12':
                pass
            pool_sequence = DoloresYear.get_pool_sequence(day, self.pools, pool_queue)
            for pool_name in pool_sequence:
                pool = self.pools[pool_name]
                pool.daily_update(day, date_str, pool_queue, logger, self.event_log,
                                  exl, inp, out, self.custom_data, dates, water_year_info)

        DoloresYear.merge_mvi_pools(logger, out, water_year_info)

        # Generate mew MVI pool totals in AF
        #
        DoloresYear.daily_update_mvi_stored(inp, out, self.units, dates)
        DoloresYear.daily_update_mvi_stored(inp, exl, self.units, dates) # Generate new pool variables in excel dict

        # MVI evaporation charge, must follow MVI pool totals generation
        #
        DoloresYear.daily_update_mvi_evap(out, dates, water_year_info)

        # Post-processing analytics
        #
        if EventLog.log_inflows:
            self.event_log.log_flow('RECORD INFLOW', exl)

        if EventLog.log_outflows:
            self.event_log.log_flow('MVI STOCK', out)
            self.event_log.log_flow('GRNDHOG DISCHARGE', inp)
            self.event_log.log_flow('LONE PINE', inp)
            self.event_log.log_flow('MVI HIGHLINE', out)
            self.event_log.log_flow('U LAT', inp)

            self.event_log.log_flow('UTE F&R', inp)
            self.event_log.log_flow('DV  CR CANAL', inp)

            self.event_log.log_flow('RECORD OTF', exl)

            self.event_log.log_flow('TOTTEN (FRESH WATER)', exl)
            self.event_log.log_flow('WET LAND', exl)
            self.event_log.log_flow('SEELEY QUEST', exl)

            self.event_log.log_flow('CORTEZ NON - PROJ', exl)
            self.event_log.log_flow('CORTEZ PROJ', exl)
            self.event_log.log_flow('UTE PROJ', exl)
            self.event_log.log_flow('MWC', exl)
            self.event_log.log_flow('F-BAY BAL', exl)

        if water_year_info.year >= 2008:
            self.event_log.log_flow('SPILL', exl)
        if water_year_info.year >= 2009:
            self.event_log.log_flow('DIST CLASS B', exl)
        if water_year_info.year >= 2015:
            self.event_log.log_flow('UF&R LEASE WATER', exl)

        if EventLog.log_fills:
            self.event_log.log_flow('NARR FILL', exl)
            if self.water_year_info.year >= 2019:
                self.event_log.log_flow('NARR FILL IN MCPHEE', exl)
            self.event_log.log_flow('U/S USERS EXCH', exl)

        path = self.file_names['water_year_log']
        year_string = str(self.water_year_info.year)
        path = Path(str(path).replace('YEAR', year_string))
        self.event_log.print_log(path, dates)
        return out

    @staticmethod
    def get_pool_sequence(day:int, pools:dict, pool_queue:PoolQueue)->list[str]:
        runs_for_day = pool_queue.get_all_runs_for_day(day)
        pool_order = []
        for run in runs_for_day:
            if run.variable_name in pools:
                if run.variable_name == 'U/S EX' and isinstance(run, FillRun):
                    pass
                else:
                    if run.end_day - 1 == day:
                        if run.variable_name not in pool_order:
                            pool_order.append(run.variable_name)
        for run in runs_for_day:
            if run.variable_name in pools:
                if run.variable_name not in pool_order:
                    pool_order.append(run.variable_name)
        for pool_name, value in pools.items():
            if pool_name not in pool_order:
                pool_order.append(pool_name)

        return pool_order

    @staticmethod
    def merge_mvi_pools(logger:UIAbstraction, out:dict, water_year_info:WaterYearInfo):
        if 2006 <= water_year_info.year <= 2021:
            if 'TO EX' in out and 'U/S EX' in out:
                out['TO EX & U/S EX'] = out['TO EX'] + out['U/S EX']
            else:
                logger.log_message(f"  FAIL TO EX & U/S EX' generating")
        elif water_year_info.year == 2005:
            if 'MVI PROJ' in out and 'TO EX' in out and 'U/S EX' in out:
                out['MVI PROJ TO EX U/S EX'] = out['MVI PROJ'] + out['TO EX'] + out['U/S EX']
            else:
                logger.log_message(f"  FAIL 'MVI PROJ TO EX U/S EX' generating")
        elif 2003 <= water_year_info.year <= 2004:
            if 'MVI CALL STOR' in out and 'TO EX' in out and 'U/S EX' in out:
                out['MVI CALL TO EX U/S EX'] = out['MVI CALL STOR'] + out['TO EX'] + out['U/S EX']
            elif 'TO EX' in out and 'U/S EX' in out:
                out['MVI CALL TO EX U/S EX'] = out['TO EX'] + out['U/S EX']
                logger.log_message(f"  Partial FAIL 'MVI CALL TO EX U/S EX' generating")
            else:
                out['MVI CALL TO EX U/S EX'] = out['MVI CALL STOR']

    @staticmethod
    def calc_narr_fill(exl, inp, out, custom_data, dates, pool_queue_all:PoolQueue):
        pool_queue = pool_queue_all.get_runs_for_variable_name('NARR FILL')

        num_days = len(inp['LONE PINE'])

        # Don't have a way to get NARR FILL targets in current water year
        # FIXME get these from CDSS for past years
        if 'NARR FILL' in exl:
            narr_fill_exl = exl['NARR FILL']
            num_days = len(narr_fill_exl)
            # narr_fill_sum = np.sum(narr_fill_exl) * WaterYear.af_to_cfs
            # date_str = WaterYearInfo.format_to_month_day(dates[num_days-1], leading_zeroes=False)
            # narr_fill_target = (date_str, narr_fill_sum)

        out['NARR FILL'] = narr_fill = WaterYear.output(num_days)
        out['NARR FILL REMAIN'] = WaterYear.output(num_days)

        fill_runs:list[FillRun] = pool_queue.get_fill_runs()
        if fill_runs:
            for fill_run in fill_runs:
                    for day in range(fill_run.start_day, fill_run.end_day + 1):
                        narr_fill[day] = inp['LONE PINE'][day]
        else:
            print(f"  NARR FILL pool queue doesn't have any fills")
            return None

        WaterYear.apply_custom_data(custom_data, 'NARR FILL', narr_fill)

        return narr_fill

    @staticmethod
    def calc_mvi_use(config, logger, exl, inp, out, custom_data, dates, water_year_info, units, narr_fill):
        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        num_days  = len(inp['LONE PINE'])

        # Dolores Tunnel and MVI HIGHLINE
        #
        tunnel_not_mvi = out['TOTAL TUNNEL Misc.'] + out['UTE F&R']

        # FIXME - Tunnel flows probably shouldn't be going negative, causes numerous downstream problems
        # May be latency of UTE F&R water from tunnel reaching TOWAOC gage, research is requires
        if not DoloresYear.patch_mvi_highline_2025_1 or water_year_info.year == 2023:
            out['MVI HIGHLINE'] = mvi_highline = WaterYear.positive_values(inp['DOLORES TUNNEL'] - tunnel_not_mvi)
        else:
            out['MVI HIGHLINE'] = mvi_highline = inp['DOLORES TUNNEL'] - tunnel_not_mvi
        units['MVI HIGHLINE'] = 'CFS'

        if water_year_info.year <= 2003:
            out['MVI/CTZ/MWC'] = out['MVI HIGHLINE'].copy()
            if water_year_info.year == 2003:
                # DWCD added MWC and CORTEZ in August 2003 so this param ends then
                aug1 = WaterYear.day_for_date(dates, 'Aug-1')
                out['MVI/CTZ/MWC'][aug1:num_days] = 0
            units['MVI/CTZ/MWC'] = 'CFS'

        mvi_use = mvi_highline + inp['LONE PINE'] + inp['U LAT']
        mvi_use = mvi_use + exl['DIST CLASS B']
        mvi_use = mvi_use + out['UF&R LEASE WATER']

        if 'TOTTEN (FRESH WATER)' in inp:
            mvi_use = mvi_use - inp['TOTTEN (FRESH WATER)']

        if narr_fill is not None:
            mvi_use = mvi_use - narr_fill

        out['MVI TOTAL WATER USED'] = WaterYear.output(num_days)
        # FIXME - This should be including stock runs before Apr-1 and after Oct-15
        # out['MVI TOTAL WATER USED'][0:oct15] = WaterYear.positive_values(mvi_use[0:oct15])
        if water_year_info.year == 2025:
            mar24 = WaterYear.day_for_date(dates, 'Mar-24')
            out['MVI TOTAL WATER USED'][mar24:oct15-1] = mvi_use[mar24:oct15-1]
            out['MVI TOTAL WATER USED'][mar24+2] = 0
        elif water_year_info.year == 2024:
            # DWCD set Apr-1 to 0, probably because this was running negative probably due to MVI Tunnel issues
            out['MVI TOTAL WATER USED'][apr1+1:oct15+1] = mvi_use[apr1+1:oct15+1]
        elif water_year_info.year == 2023:
            out['MVI TOTAL WATER USED'][apr1+10:oct15-1] = mvi_use[apr1+10:oct15-1]
            oct13 = WaterYear.day_for_date(dates, 'Oct-13')
            fbay = inp['DOLORES TUNNEL'][oct13] - (exl['MWC'][oct13] + exl['CORTEZ NON - PROJ'][oct13]
                                                    + exl['UTE PROJ'][oct13] + exl['UTE F&R'][oct13])
            out['MVI TOTAL WATER USED'][oct13] = out['MVI TOTAL WATER USED'][oct13] + fbay
        elif water_year_info.year == 2003:
            # MWC and CTZ were added in August which reduced MVI total use for those months
            aug1 = WaterYear.day_for_date(dates, 'Aug-1')
            oct31 = WaterYear.day_for_date(dates, 'Oct-31')+1
            mvi_use[aug1:oct31] -= (exl['CTZ'][aug1:oct31] + exl['CTZ PROJ'][aug1:oct31])
            out['MVI TOTAL WATER USED'] = mvi_use
        else:
            out['MVI TOTAL WATER USED'] = mvi_use

        if DoloresYear.patch_mvi_use_1:
            # Water Resources Tech:
            # -12.5 CFS flow was removed here to avoid crediting MVIC with excess fill into canal from Hermana.
            # This takes account for the new USGS numbers updated May 6th, 2025
            WaterYear.correction(out, 4, 7, 'MVI TOTAL WATER USED', 9.357)

        mvi_stock = DoloresYear.run_mvi_stock_runs(config, logger, exl, out, custom_data, dates)
        if 'MVI TOTAL IRRIG' in exl:
            out['MVI TOTAL IRRIG'] = out['MVI TOTAL WATER USED'] - mvi_stock

        # How much MVI Call water is available for pool fills(aka storage)
        # When it goes negative how much needs to be drained from available pools
        #
        mvi_storable = DoloresYear.calc_mvi_storable(exl, inp, dates, water_year_info)
        mvi_storable[:apr1] = 0.0
        if water_year_info.year == 2002:
            mvi_storable[oct15+2:] = 0.0
        elif water_year_info.year == 2023:
            pass
        elif water_year_info.year == 2015:
            jun4 = WaterYear.day_for_date(dates, 'Jun-4')
            jul1 = WaterYear.day_for_date(dates, 'Jul-1')
            mvi_storable[jun4:jul1] = 0.0
        else:
            mvi_storable[oct15+1:] = 0.0

        out['MVI STORABLE'] = mvi_storable

    @staticmethod
    def run_mvi_stock_runs(config, logger, exl, out, custom_data, dates):
        narr_fill = exl['NARR FILL']
        num_days  = len(narr_fill)

        mvi_stock = out['MVI STOCK'] = WaterYear.output(num_days)
        mvi_stock_runs = WaterYear.get_flow_runs(config, logger, 'MVI STOCK')
        if mvi_stock_runs is not None:
            for mvi_stock_run in mvi_stock_runs:
                start_day = WaterYear.day_for_date(dates, mvi_stock_run[0])
                end_day = WaterYear.day_for_date(dates, mvi_stock_run[1])
                if len(mvi_stock_run) > 2:
                    variable_names = mvi_stock_run[2]
                    for day in range(start_day, end_day + 1):
                        cfs = 0
                        for variable_name in variable_names:
                            if variable_name == 'MVI HIGHLINE':
                                cfs += out[variable_name][day]
                            else:
                                cfs += exl[variable_name][day]
                        if cfs > 0:  # MVI Tunnel going negative can cancel out the entire days stock run, including LP and U(ref 2025 mar-26)
                            mvi_stock[day] = cfs
            WaterYear.apply_custom_data(custom_data, 'MVI STOCK', mvi_stock)

        return mvi_stock

    @staticmethod
    def calc_mvi_storable(exl, inp, dates, water_year_info):
        outflow_adj = exl['MWC'] + exl['CORTEZ NON - PROJ'] + inp['D/S SENIOR MVIC']
        mask_gt_795 = np.array(exl['RECORD INFLOW'] >= (795 + outflow_adj))
        mvi_storable = np.where(mask_gt_795,
                 795 - exl['MVI TOTAL WATER USED'] - exl['SPILL'],
                 exl['RECORD INFLOW'] - outflow_adj - exl['MVI TOTAL WATER USED'] - exl['SPILL'])
        if water_year_info.year == 2024:
            apr25 = WaterYear.day_for_date(dates, 'Apr-25')
            mvi_storable[apr25] = mvi_storable[apr25] + exl['NARR FILL'][apr25]
            may1 = WaterYear.day_for_date(dates, 'May-1')
            mvi_storable[may1] = mvi_storable[may1] - exl['NARR FILL'][may1]
            jun6 = WaterYear.day_for_date(dates, 'Jun-6')
            mvi_storable[jun6:jun6+5] = mvi_storable[jun6:jun6+5] - exl['NARR FILL'][jun6:jun6+5]

        return mvi_storable

    @staticmethod
    def mvi_dist_class_b(config, logger, out, dates, water_year_info):
        num_days = len(dates)
        out['DIST CLASS B'] = dist_class_b = WaterYear.output(num_days)
        dist_class_b_runs = WaterYear.get_flow_runs(config, logger, 'DIST CLASS B')
        if not dist_class_b_runs or water_year_info.year < 2002:
            return

        may10 = WaterYear.day_for_date(dates, 'May-10')
        jun1 = WaterYear.day_for_date(dates, 'Jun-1')
        jul1 = WaterYear.day_for_date(dates, 'Jul-1')
        aug1 = WaterYear.day_for_date(dates, 'Aug-1')
        sep1 = WaterYear.day_for_date(dates, 'Sep-1')

        for day in range(may10, num_days):
            if may10 <= day < jun1:
                dist_class_b[day] = 280.641404351437 / WaterYear.af_to_cfs / 22
            elif jun1 <= day < jul1:
                dist_class_b[day] = 646.095 / WaterYear.af_to_cfs / 30
            elif jul1 <= day < aug1:
                dist_class_b[day] = 1121.512 / WaterYear.af_to_cfs / 31

        class_b_af = WaterYear.get_config(config, '', 'DIST CLASS B')
        dist_so_far = np.sum(dist_class_b)
        dist_left = class_b_af / WaterYear.af_to_cfs - dist_so_far
        dist_daily = dist_left / 31
        for day in range(aug1, sep1):
            dist_class_b[day] = dist_daily

    @staticmethod
    def daily_update_mvi_stored(inp, out, units, dates):
        # Outputs
        num_days = len(dates)
        out['MVI POOL MCPHEE NON PROJ'] = WaterYear.get_out('MVI POOL MCPHEE NON PROJ', out, num_days)
        units['MVI POOL MCPHEE NON PROJ'] = 'AF'
        out['MVI POOL MCPHEE TOTAL'] = WaterYear.get_out('MVI POOL MCPHEE TOTAL', out, num_days)
        units['MVI POOL MCPHEE TOTAL'] = 'AF'
        out['MVI POOL TOTAL'] = WaterYear.get_out('MVI POOL TOTAL', out, num_days)
        units['MVI POOL TOTAL'] = 'AF'

        for day in range(0, num_days):
            date_str = WaterYearInfo.format_to_month_day(dates[day])
            if date_str == 'Jun-23':
                pass
            mvi_total_pool_cfs = 0
            if 'MVI CALL TO EX U/S EX' in out:
                mvi_total_pool_cfs += out['MVI CALL TO EX U/S EX'][day]
            elif 'MVI CALL STOR' in out:
                mvi_total_pool_cfs += out['MVI CALL STOR'][day]
            else:
                mvi_total_pool_cfs += out['MVI CALL STOR'][day]

            if 'TO EX & U/S EX' in out:
                mvi_total_pool_cfs += out['TO EX & U/S EX'][day]
            else:
                if 'TO EX' in out:
                    mvi_total_pool_cfs += out['TO EX'][day]
                if 'U/S EX' in out:
                    mvi_total_pool_cfs += out['U/S EX'][day]

            if 'NARR CALL' in out:  # Narr water stored in McPhee circa 2003-2008
                mvi_total_pool_cfs += out['NARR CALL'][day]
            elif 'CUM NARR IN MCPHEE' in out:  # Narr water stored in McPhee circa 2019-Present
                mvi_total_pool_cfs += out['CUM NARR IN MCPHEE'][day]
            out['MVI POOL MCPHEE NON PROJ'][day] = mvi_total_pool_cfs * WaterYear.af_to_cfs

            if 'MVI PROJ' in out:
                mvi_total_pool_cfs += out['MVI PROJ'][day]
            out['MVI POOL MCPHEE TOTAL'][day] = mvi_total_pool_cfs * WaterYear.af_to_cfs

            if 'GRNDHOG CAPACITY' in inp:
                mvi_total_pool_cfs += inp['GRNDHOG CAPACITY'][day]
            if 'NARR CAPACITY' in inp:
                mvi_total_pool_cfs += inp['NARR CAPACITY'][day]
            out['MVI POOL TOTAL'][day] = mvi_total_pool_cfs * WaterYear.af_to_cfs

    @staticmethod
    def daily_update_mvi_evap(out, dates, water_year_info):
        # Outputs
        num_days = len(dates)
        out['MVI STORED EVAP'] = WaterYear.get_out('MVI STORED EVAP', out, num_days)

        apr1 = WaterYear.day_for_date(dates, 'Apr-01')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')
        for day in range(apr1, oct15+1):
            if 'MVI CALL TO EX U/S EX' in out:
                out['MVI STORED EVAP'][day]  = (23.5 * (
                            out['MVI CALL TO EX U/S EX'][day] * 1.9835 - out['MVI TOTAL WATER USED'][day] * 1.9835)
                                                / out['ACTIVE CAP'][day])
                # out['MVI STORED EVAP'][0:apr1] = 0.0
            else:
                jun29 = WaterYear.day_for_date(dates, 'Jun-29')
                if water_year_info.year == 2023 and apr1 <= day <= jun29:
                    # Call water and Narr in McPhee are going to be spilled so no evap charges are being taken
                    out['MVI STORED EVAP'][day] = (out['LAKE EVAP VOL'][day] * (out['TO EX'][day] * WaterYear.af_to_cfs) / out['ACTIVE CAP'][day])
                else:
                    out['MVI STORED EVAP'][day] = (out['LAKE EVAP VOL'][day] * out['MVI POOL MCPHEE NON PROJ'][day]
                                          / out['ACTIVE CAP'][day])

    @staticmethod
    def run_spill_runs(config, logger, exl, out, custom_data, dates):
        below_mcp = exl['BELOW MCP']
        num_days  = len(below_mcp)

        spill = out['SPILL'] = WaterYear.output(num_days)
        spill_runs = WaterYear.get_flow_runs(config, logger, 'SPILL')
        if spill_runs is not None:
            for spill_run in spill_runs:
                start_day = WaterYear.day_for_date(dates, spill_run[0])
                end_day = WaterYear.day_for_date(dates, spill_run[1])
                for day in range(start_day, end_day + 1):
                    spill[day] = below_mcp[day]

            WaterYear.apply_custom_data(custom_data, 'SPILL', spill)

        return spill

    @staticmethod
    def calc_fish_pool_left(config, exl, inp, dates, water_year_info):
        below_mcphee = inp['BELOW MCP']
        spill = exl['SPILL']

        fish_pool_left_oct31_af = WaterYear.get_config(config, 'oct31', 'FISH LEFT')
        fish_pool_left_apr1_af = WaterYear.get_config(config, '', 'fish_pool_left_apr1_af')

        fish_left = WaterYear.output(len(below_mcphee))
        feb28 = WaterYear.day_for_date(dates, 'Feb-28')
        mar1 = WaterYear.day_for_date(dates, 'Mar-1')
        apr1 = WaterYear.day_for_date(dates, 'Apr-1')

        fish_left[0] = fish_pool_left_oct31_af - below_mcphee[0] - spill[0]
        for day in range(1, len(below_mcphee)):
            if day == apr1:
                fish_left[day] = fish_pool_left_apr1_af - below_mcphee[day] - spill[day]
            else:
                below_mcp = below_mcphee[day]
                if below_mcp > spill[day]:
                    below_mcp -= spill[day]
                else:
                    below_mcp = 0
                if water_year_info.year == 2024 and day == mar1:
                    fish_left[day] = fish_left[feb28] - below_mcp
                else:
                    fish_left[day] = fish_left[day - 1] - below_mcp
        return fish_left

    @staticmethod
    def calc_mvi_class_a_lease(config, logger, out, inp, dates):
        num_days = len(inp['LONE PINE'])
        out['UF&R LEASE WATER'] = ufr_lease = WaterYear.output(num_days)

        ufr_class_a_shares_af = config.get('UF&R LEASE WATER')

        mvi_ufr_lease_runs = WaterYear.get_flow_runs(config, logger, 'UF&R LEASE WATER')
        if ufr_class_a_shares_af is not None and isinstance(ufr_class_a_shares_af, int) or isinstance(ufr_class_a_shares_af, float):
            # FIXME	 2025-08-24 to 2025-08-25
            # 		+ =(exl['UF&R LEASE WATER'][day-29]-(SUM(exl['UF&R LEASE WATER'][day-23]:exl['UF&R LEASE WATER'][day-1])*1.9835))/1.9835
            remaining_cfs = ufr_class_a_shares_af / WaterYear.af_to_cfs
            for start_date, end_date in mvi_ufr_lease_runs:
                start_day = WaterYear.day_for_date(dates, start_date)
                end_day = WaterYear.day_for_date(dates, end_date)
                for day in range(start_day, end_day+1):
                    if remaining_cfs:
                        cfs_used = out['UTE F&R'][day]
                        if cfs_used > remaining_cfs:
                            cfs_used = remaining_cfs
                        remaining_cfs -= cfs_used
                        ufr_lease[day] = cfs_used

    @staticmethod
    def cumulative_fill_after_day(arr, idx):
        # Create a copy of the input array to avoid modifying it
        result = np.copy(arr)
        # Set elements before idx to 0
        result[:idx] = 0
        # Subtract the value at idx from elements after idx
        if idx > 0:
            result[idx:] = result[idx:] - arr[idx-1]
        result[result < 0] = 0
        return result

    @staticmethod
    def calc_tunnel_flows(inp, out, dates, custom_data, water_year_info):
        num_days = len(dates)
        out['CORTEZ NON - PROJ'] = WaterYear.output(num_days)
        out['CORTEZ PROJ'] = WaterYear.output(num_days)

        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        sep1 = WaterYear.day_for_date(dates, 'Sep-1')
        oct1 = WaterYear.day_for_date(dates, 'Oct-1')

        # Ute Farm and Ranch, this is synonymous with DWR CDSS Towaoc canal flow, with 1.05 adjustment removed
        out['UTE F&R'] = inp['UTE F&R CFS'] * 1.05
        WaterYear.apply_custom_data(custom_data, 'UTE F&R', out['UTE F&R'])

        # Montezuma Water Company project water
        #
        result = (inp['MWC CFS']) * 1.02
        WaterYear.apply_custom_data(custom_data, 'MWC', result)
        out['MWC'] = result

        # Ute Project water, I think this is Towaoc Domestic water via Cortez treatment plant
        #
        result = (inp['UTE PROJ CFS'] * 1.06) * 1.04
        WaterYear.apply_custom_data(custom_data, 'UTE PROJ', result)
        out['UTE PROJ'] = result

        # City of Cortez Non Project water
        result = (inp['CORTEZ NON - PROJ CFS'] * 1.04) - out['UTE PROJ']
        if DoloresYear.patch_cortez_non_proj_2025_1:
            # FIXME - this changed from 1.04 to 1.02, 1.02 is the MWC factor, and is using gallons instead of the standard formula
            result[sep1:oct1] = inp['CORTEZ NON - PROJ CFS'][sep1:oct1] * 1.02
        result = np.maximum(result, 0)
        result[result > 4.2] = 4.2
        WaterYear.apply_custom_data(custom_data, 'CORTEZ NON - PROJ', result)
        out['CORTEZ NON - PROJ'] = result

        # City of Cortez Project water
        # 'CORTEZ PROJ'
        result = (inp['CORTEZ PROJ CFS'] * 1.04) - out['UTE PROJ']
        if water_year_info.year == 2015:
            result = result - 4.2
        else:
            result[apr1:] = result[apr1:] - 4.2
        result[apr1:] = np.maximum(result[apr1:], 0)
        result[result > 4.2] = 4.2
        WaterYear.apply_custom_data(custom_data, 'CORTEZ PROJ', result)
        out['CORTEZ PROJ'] = result

    @staticmethod
    def calc_dwcd(out, exl, inp, dates):
        num_days = len(dates)
        out['DWCD 505 FLOWS AVAIL'] = available = WaterYear.output(num_days)

        record_inflow = out['RECORD INFLOW']

        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        may1 = WaterYear.day_for_date(dates, 'May-1')
        sep1 = WaterYear.day_for_date(dates, 'Sep-1')
        oct1 = WaterYear.day_for_date(dates, 'Oct-1')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        for day in range(0, num_days):
            # 'DWCD 505 FLOWS AVAIL'
            # FIXME - Not sure what the formula in September is doing
            floor = 795 + exl['MWC'][day] + exl['CORTEZ NON - PROJ'][day] + inp['D/S SENIOR MVIC'][day] + inp['D/S SENIOR PROJ'][day]
            if apr1 <= day < sep1:
                if record_inflow[day] > floor:
                    available[day] = record_inflow[day] - floor
            if sep1 <= day < oct1:
                if record_inflow[day] > floor:
                    available[day] = record_inflow[day] - floor
            elif day < oct15:
                if record_inflow[day] > floor:
                    available[day] = record_inflow[day] - floor

        # 'DWCD 505 CFS DIRECT DIV'
        # FIXME - Not sure what the formula in September is doing
        diverted = out['UTE F&R'] + inp['DV  CR CANAL']
        out['DWCD 505 CFS DIRECT DIV'] = diversion = np.minimum(available, diverted)
        for day in range(may1, sep1):
            result = np.min([505, available[day], diverted[day]])
            diversion[day] = result

        # Not used, maybe debugging 'BELOW MCP'
        #
        # out['BELOW MCP MPP from ctrl room'] = WaterYear.output(num_days)
        # out['BELOW MCP OVER MPP'] = WaterYear.output(num_days)

    @staticmethod
    def drain_mvi_pool(logger, event_log, drain_run:DrainRun, out, dates, storable_cfs:np.ndarray, pool_queue_all:PoolQueue):
        variable_name = drain_run.variable_name
        pool_cfs = out[variable_name]
        start_day = drain_run.start_day
        if start_day < len(pool_cfs):
            pool_af = pool_cfs[start_day] * WaterYear.af_to_cfs
            print(f'\tDraining {variable_name} {pool_af} af')
        else:
            return

        num_days = len(pool_cfs)
        if EventLog.log_drains:
            event_log.log(start_day, variable_name, f'Start  drain                  inp {pool_af:7.1f} AF')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        # Upstream exchange can fill and drain at the same time, this preserves the fill
        fills = WaterYear.compute_float_diffs(logger, drain_run.variable_name, pool_cfs, 0)

        remaining = 0
        end_day = oct15
        if drain_run is not None and drain_run.end_day:
            end_day = drain_run.end_day
            if end_day == oct15:
                # FIXME - This fix for 2024 is suspect, end_day is already adding 1 in the for loop
                end_day = oct15+1

        end_runs: list[DrainRun] = pool_queue_all.get_completed_on_day(drain_run.start_day)
        if end_runs:
            pool_cfs[drain_run.start_day - 1] = pool_cfs[drain_run.start_day - 2] - end_runs[0].complete_remaining_cfs
        last_day = None
        for day in range(start_day, end_day+1):
            if day > oct15:
                pool_cfs[day] = 0.0
                last_day = oct15+1
                continue
            # if last_remaining:
                # If previous pool finished draining and satisfied some of the daily drain
                # we just finish draining what was left over from that drain first time through
                # drain = last_remaining
                # last_remaining = 0
            # else:
            drain = -storable_cfs[day]

            # Upstream exchange can fill and drain at the same time, this preserves the fill
            fill = fills[day]
            pool = pool_cfs[day-1] + fill
            if drain > 0:
                if drain < pool:
                    pool_cfs[day] = pool - drain
                else:
                    # Draining this pool is done, shut it down and move to the next
                    remaining = pool - drain
                    pool_cfs[day] = 0
                    last_day = day
                    drain_run.ending(logger, last_day, remaining)
                    break
            else:
                # MVI isn't using water so just propagate last value
                pool_cfs[day] = pool

        if last_day is not None:
            end_day = last_day
            for day in range(end_day, oct15+1):
                pool_cfs[day] = 0.0
        elif end_day:
            for day in range(end_day, oct15+1):
                pool_cfs[day] = pool_cfs[day-1]
        else:
            pass

        for day in range(oct15+1, num_days):
            pool_cfs[day] = 0.0

        if last_day is not None:
            pool_af = pool_cfs[last_day] * WaterYear.af_to_cfs
            if EventLog.log_drains:
                event_log.log(last_day, variable_name, f'Ending drain                  out {remaining:7.2f} cfs {pool_af:7.1f} AF {last_day-start_day:7d} days', is_ending=True)
        else:
            pool_af = pool_cfs[num_days-1] * WaterYear.af_to_cfs
            no_remainder = ' '
            continue_day = num_days-1-start_day
            if EventLog.log_drains:
                event_log.log(num_days-1, variable_name, f'Draining                        {no_remainder:7}     {pool_af:7.1f} AF {continue_day:7d} days', is_ending=True)

        return



