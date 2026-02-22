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
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FsROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import numpy as np
import json
from pathlib import Path
from dwcd.water_year import WaterYear

class DoloresYear(WaterYear):
    patch_cum_narr_in_mcphee_2025_1 = True
    patch_cum_narr_in_mcphee_2025_2 = True
    patch_mvi_use_1 = True
    patch_mvi_tunnel_2025_1 = True
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
        'F-BAY BAL': ['DOL TUN TOT DIV', 'MWC NON - PROJ', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ'],
        'MVI TUNNEL': ['DOL TUN TOT DIV', 'WET LAND', 'UTE F&R', 'SEELEY', 'MWC NON - PROJ', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ', 'F-BAY BAL'],
        'TOTAL MVI WATER USED': ['MVI TUNNEL', 'LONE PINE', 'U LAT', 'TOTTEN (FRESH WATER)', 'DIST CLASS B', 'NARR FILL'],
        'TOTAL MVI IRRIG. WATER USED': ['TOTAL MVI WATER USED', 'MVI STOCK'],
        'MVI CALL STOR': ['DOLORES RIVER', 'RECORD INFLOW', 'TOTAL MVI WATER USED', 'UF&R LEASE WATER', 'U/S USERS EXCH', 'D/S SENIOR MVIC', 'SPILL', 'TO EX'],
        'MVI CALL SPILLED OR USED': [], # FIXME
        'MVI APR- JUNE (DIV+ CALL)': [], # FIXME
        'TO EX': ['MVI STORABLE', 'CUM NARR IN MCPHEE', 'MVI STORED EVAP'],
        'MVI PROJ': ['MVI STORABLE', 'U/S EX'],
        'SPILL': ['BELOW MCP'],
        'FISH LEFT': ['BELOW MCP', 'SPILL'],
        'RECORD OTF': ['WET LAND', 'UTE F&R', 'SEELEY','MWC NON - PROJ', 'CORTEZ NON - PROJ', 'CORTEZ PROJ', 'UTE PROJ', 'F-BAY BAL', 'TOTAL MVI WATER USED', 'DV  CR CANAL', 'BELOW MCP'],
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
        'TOTAL TUNNEL Misc.': ['WET LAND', 'SEELEY', 'F-BAY BAL'],
        'LAKE EVAP': ['PAN EVAP'],
        'LAKE EVAP VOL': ['LAKE EVAP', 'LAKE SURFACE AREA'],
        'DWCD 505 FLOWS AVAIL': [], # FIXME
        'DWCD 505 CFS DIRECT DIV': ['DWCD 505 FLOWS AVAIL', 'UTE F&R', 'DV  CR CANAL', 'MVIC DAILY POOL USED']
    }

    def __init__(self, ui_abstraction):
        super().__init__(ui_abstraction)

    def run(self):
        if self.water_year_info.year != 2025:
            DoloresYear.patch_cum_narr_in_mcphee_2025_1 = False
            DoloresYear.patch_cum_narr_in_mcphee_2025_2 = False
            DoloresYear.patch_mvi_use_1 = False
            DoloresYear.patch_mvi_tunnel_2025_1 = True
            DoloresYear.patch_cortez_non_proj_2025_1 = False
        if self.water_year_info.year != 2024:
            DoloresYear.patch_to_ex_2024_1 = False

        self.config['logger'] = self.logger
        self.calc = self.calc_water_year(self.water_year_info, self.logger, self.n, self.inputs_dwcd, self.inputs_cdss, self.config)

        with self.file_names['units_json'].open("w") as file:
            json.dump(self.units, file, indent=4)

        unimplemented = list(WaterYear.remove_keys_from_dict(self.n, self.inputs_dwcd, self.calc))
        results = WaterYear.check_arrays_zero_or_nan(self.n, unimplemented)

        really_unimplemented = []
        for key, is_zero in results.items():
            if not is_zero:
                if len(key) == 2 and key[0] == 'B':
                    # Columns with no variable, probably have debug stuff in them
                    pass
                else:
                    really_unimplemented.append(key)
            else:
                pass

        if len(really_unimplemented):
            for key in really_unimplemented:
                self.logger.log_message(f'  Unimplemented: {key}')

    def calc_water_year(self, water_year_info, logger, exl, inp, inp_cdss, config):
        water_year = water_year_info.year
        WaterYear.start_log()
        print("Run Water Year", water_year)
        out = {}

        ute_farms_loss_adj = 1.05
        config['upstream_user_exchange_af'] = 1641

        out['DATE'] = dates = exl['DATE']

        WaterYear.pre_process(logger, exl, inp, dates)

        # Parameters that may be specific to 2025 water year
        #
        narr_in_mcphee_fill_target_af = 5457.172

        # MVI Pool Drain order (may be obsoleted)
        #
        if water_year_info.year == 2024:
            mvi_pool_drain_order = [
            ]
        else:
            mvi_pool_drain_order = [
                'CUM NARR IN MCPHEE',
                'U/S EX',
                'MVI PROJ',
                'TO EX',
            ]
        # End parameters

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

        # Tunnel
        #
        DoloresYear.calc_tunnel_flows(inp, out, dates)
        out['DOMESTIC'] = exl['MWC NON - PROJ'] + exl['CORTEZ NON - PROJ'] + exl['CORTEZ PROJ'] + out['UTE PROJ']
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
                out['F-BAY BAL'][day_begins:day_ends+1] = inp['DOL TUN TOT DIV'][day_begins:day_ends+1] - out['DOMESTIC'][day_begins:day_ends+1]
        out['DOMESTIC'] = out['DOMESTIC'] + out['F-BAY BAL']

        out['GATE 504'] = inp['WET LAND'] + inp['SEELEY']  # FIXME Totten Fresh Water is here too?
        self.units['GATE 504'] = 'CFS'
        out['TOTAL TUNNEL Misc.'] = out['GATE 504'] + out['DOMESTIC']

        # Finish Inflow/Outflow
        #
        out['RECORD OTF'] = inp['DOL TUN TOT DIV'] + inp['LONE PINE'] + inp['U LAT'] + inp['DV  CR CANAL'] + inp['BELOW MCP']
        if water_year_info.year == 2024:
            # FIXME - Hack to get 2024 RECORD OTF to balance
            out['RECORD OTF'][0:apr1-15] = out['RECORD OTF'][0:apr1-15] - exl['NARR FILL'][0:apr1-15]
        elif water_year_info.year == 2023:
            # FIXME - Hack to get 2023 RECORD OTF to balance
            out['RECORD OTF'][0:apr1+3] = out['RECORD OTF'][0:apr1+3] - exl['NARR FILL'][0:apr1+3]
            out['RECORD OTF'][0:apr1+10] = out['RECORD OTF'][0:apr1+10] + exl['UTE F&R'][0:apr1+10]

            fbay = WaterYear.output(num_days)
            oct31 = WaterYear.day_for_date(dates, 'Oct-31')
            fbay[apr1:oct31+1] = inp['DOL TUN TOT DIV'][apr1:oct31+1] - (exl['MWC NON - PROJ'][apr1:oct31+1]
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
        out['FISH LEFT'] = DoloresYear.calc_fish_pool_left(config, logger, exl, inp, dates, water_year_info)

        # DWCD 505 Water Right
        #
        DoloresYear.calc_dwcd(config, logger, out, exl, inp, dates)

        # MVI Ute Lease Water
        #
        DoloresYear.calc_mvi_class_a_lease(config, logger, out, inp, dates)

        start_upstream_exchange_drain_day, remaining = DoloresYear.fill_mvi_upstream_exchange(config, logger, out, inp, dates)

        # MVI Class B water
        #
        DoloresYear.mvi_dist_class_b(config, logger, out, dates, water_year_info)

        # MVI Usage
        #
        DoloresYear.calc_mvi_use(config, logger, exl, inp, out, self.custom_data, dates, water_year_info, self.units, water_year)

        # MVI evaporation charge
        #
        # exl['LAKE EVAP VOL'][day]*((exl['MVI CALL STOR'][day]+exl['TO EX'][day]+exl['U/S EX'][day]+exl['CUM NARR IN MCPHEE'][day])*1.9835)/exl['ACTIVE CAP'][day]
        out['MVI STORED'] = (exl['MVI CALL STOR'] + exl['TO EX'] + exl['U/S EX'] + exl['CUM NARR IN MCPHEE']) * WaterYear.af_to_cfs
        self.units['MVI STORED'] = 'CFS'
        out['MVI STORED EVAP'] = out['LAKE EVAP VOL'] * out['MVI STORED'] / out['ACTIVE CAP']

        # MVI Pool Filling
        #
        narr_fill_last_day,  narr_fill_remaining_cfs = (
            DoloresYear.fill_mvi_narraguinnep_in_mcphee(config, logger, exl, inp, out, self.custom_data, dates,
                                                        water_year_info, narr_in_mcphee_fill_target_af))

        DoloresYear.run_mvi_totten_exchange(config, logger, out, exl, inp, dates, water_year_info,
                                             narr_fill_last_day, narr_fill_remaining_cfs)

        # MVI Call Water (72,000 af, Apr1-Jun30)
        #
        last_day, remaining = DoloresYear.fill_mvi_call_water(config, logger, out, exl, inp, self.comments, dates)

        # Drain MVI pools in user specified order
        #
        storable = exl['MVI STORABLE']
        for pool_name in mvi_pool_drain_order:
            last_day, remaining = DoloresYear.drain_mvi_pool(pool_name, out, dates, storable, last_day, remaining)
            if last_day < len(dates):
                last_date = dates[last_day]
            else:
                break

        # Post processing analytics
        #
        if WaterYear.log_inflows:
            WaterYear.log_flow('RECORD INFLOW', exl)

        if WaterYear.log_outflows:
            WaterYear.log_flow('MVI STOCK', out)
            WaterYear.log_flow('GRNDHOG DISCHARGE', inp)
            WaterYear.log_flow('LONE PINE', inp)
            WaterYear.log_flow('MVI TUNNEL', out)
            WaterYear.log_flow('U LAT', inp)

            WaterYear.log_flow('UTE F&R', inp)
            WaterYear.log_flow('DV  CR CANAL', inp)

            WaterYear.log_flow('RECORD OTF', exl)

            WaterYear.log_flow('TOTTEN (FRESH WATER)', exl)
            WaterYear.log_flow('WET LAND', exl)
            WaterYear.log_flow('SEELEY', exl)

            WaterYear.log_flow('CORTEZ NON - PROJ', exl)
            WaterYear.log_flow('CORTEZ PROJ', exl)
            WaterYear.log_flow('UTE PROJ', exl)

        WaterYear.log_flow('SPILL', exl)
        WaterYear.log_flow('MWC NON - PROJ', inp)
        WaterYear.log_flow('F-BAY BAL', exl)
        if water_year_info.year >= 2002:
            WaterYear.log_flow('DIST CLASS B', exl)
        WaterYear.log_flow('UF&R LEASE WATER', exl)

        if WaterYear.log_fills:
            WaterYear.log_flow('NARR FILL', exl)
            WaterYear.log_flow('NARR FILL IN MCPHEE', exl)
            WaterYear.log_flow('U/S USERS EXCH', exl)

        path = self.file_names['water_year_log']
        year_string = str(self.water_year_info.year)
        path = Path(str(path).replace('YEAR', year_string))
        WaterYear.print_log(path, dates)
        return out

    @staticmethod
    def calc_mvi_use(config, logger, exl, inp, out, custom_data, dates, water_year_info, units, water_year):
        print('\tMVI Use')
        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        num_days  = len(inp['LONE PINE'])

        tunnel_not_mvi = out['TOTAL TUNNEL Misc.'] + out['UTE F&R']
        # FIXME - Tunnel flows probably shouldn't be going negative, causes numerous downstream problems
        # May be latency of UTE F&R water from tunnel reaching TOWAOC gage, research is requires
        if not DoloresYear.patch_mvi_tunnel_2025_1 or water_year_info.year == 2023:
            out['MVI TUNNEL'] = mvi_tunnel = WaterYear.positive_values(inp['DOL TUN TOT DIV'] - tunnel_not_mvi)
        else:
            out['MVI TUNNEL'] = mvi_tunnel = inp['DOL TUN TOT DIV'] - tunnel_not_mvi
        units['MVI TUNNEL'] = 'CFS'

        mvi_use = mvi_tunnel + inp['LONE PINE'] + inp['U LAT']
        mvi_use = mvi_use + exl['DIST CLASS B']
        mvi_use = mvi_use + out['UF&R LEASE WATER']

        if 'TOTTEN (FRESH WATER)' in inp:
            mvi_use = mvi_use - inp['TOTTEN (FRESH WATER)']

        out['NARR FILL'] = narr_fill = WaterYear.output(num_days)
        out['NARR FILL REMAIN'] = WaterYear.output(num_days)
        narr_fill_runs = WaterYear.get_flow_runs(config, logger, 'NARR FILL')
        if narr_fill_runs is not None:
            for narr_fill_run in narr_fill_runs:
                    start_day = WaterYear.day_for_date(dates, narr_fill_run[0])
                    end_day = WaterYear.day_for_date(dates, narr_fill_run[1])
                    for day in range(start_day, end_day + 1):
                        narr_fill[day] = inp['LONE PINE'][day]
        WaterYear.apply_custom_data(custom_data, 'NARR FILL', narr_fill)
        mvi_use = mvi_use - exl['NARR FILL']

        out['TOTAL MVI WATER USED'] = WaterYear.output(num_days)
        # FIXME - This should be including stock runs before Apr-1 and after Oct-15
        # out['TOTAL MVI WATER USED'][0:oct15] = WaterYear.positive_values(mvi_use[0:oct15])
        if water_year_info.year == 2025:
            mar24 = WaterYear.day_for_date(dates, 'Mar-24')
            out['TOTAL MVI WATER USED'][mar24:oct15-1] = mvi_use[mar24:oct15-1]
            out['TOTAL MVI WATER USED'][mar24+2] = 0
        elif water_year_info.year == 2024:
            # DWCD set Apr-1 to 0, probably because this was running negative probably due to MVI Tunnel issues
            out['TOTAL MVI WATER USED'][apr1+1:oct15+1] = mvi_use[apr1+1:oct15+1]
        elif water_year_info.year == 2023:
            out['TOTAL MVI WATER USED'][apr1+10:oct15-1] = mvi_use[apr1+10:oct15-1]
            oct13 = WaterYear.day_for_date(dates, 'Oct-13')
            fbay = inp['DOL TUN TOT DIV'][oct13] - (exl['MWC NON - PROJ'][oct13] + exl['CORTEZ NON - PROJ'][oct13]
                                                    + exl['UTE PROJ'][oct13] + exl['UTE F&R'][oct13])
            out['TOTAL MVI WATER USED'][oct13] = out['TOTAL MVI WATER USED'][oct13] + fbay
        else:
            out['TOTAL MVI WATER USED'][apr1:oct15+1] = mvi_use[apr1:oct15+1]

        if DoloresYear.patch_mvi_use_1:
            # Water Resources Tech:
            # -12.5 CFS flow was removed here to avoid crediting MVIC with excess fill into canal from Hermana.
            # This takes account for the new USGS numbers updated May 6th, 2025
            WaterYear.correction(out, 4, 7, 'TOTAL MVI WATER USED', 9.357)

        mvi_stock = DoloresYear.run_mvi_stock_runs(config, logger, exl, out, custom_data, dates)
        out['TOTAL MVI IRRIG. WATER USED'] = out['TOTAL MVI WATER USED'] - mvi_stock

        mvi_storable = DoloresYear.calc_mvi_storable(exl, inp, out, dates, water_year_info)
        mvi_storable[:apr1] = 0.0
        if water_year_info.year != 2023:
            mvi_storable[oct15+1:] = 0.0
        out['MVI STORABLE'] = mvi_storable

    @staticmethod
    def run_mvi_stock_runs(config, logger, exl, out, custom_data, dates):
        narr_fill = exl['NARR FILL']
        num_days  = len(narr_fill)

        mvi_stock = out['MVI STOCK'] = WaterYear.output(num_days)
        mvi_stock_runs = WaterYear.get_flow_runs(config, logger, 'MVI STOCK')
        for mvi_stock_run in mvi_stock_runs:
            start_day = WaterYear.day_for_date(dates, mvi_stock_run[0])
            end_day = WaterYear.day_for_date(dates, mvi_stock_run[1])
            if len(mvi_stock_run) > 2:
                variable_names = mvi_stock_run[2]
                for day in range(start_day, end_day + 1):
                    cfs = 0
                    for variable_name in variable_names:
                        if variable_name == 'MVI TUNNEL':
                            cfs += out[variable_name][day]
                        else:
                            cfs += exl[variable_name][day]
                        if variable_name == 'LONE PINE' or variable_name == 'TOTAL MVI WATER USED':
                            out['NARR FILL'][day] = 0.0
                    if cfs > 0:  # MVI Tunnel going negative can cancel out the entire days stock run, including LP and U(ref 2025 mar-26)
                        mvi_stock[day] = cfs
        WaterYear.apply_custom_data(custom_data, 'MVI STOCK', mvi_stock)

        return mvi_stock

    @staticmethod
    def calc_mvi_storable(exl, inp, out, dates, water_year_info):
        outflow_adj = exl['MWC NON - PROJ'] + exl['CORTEZ NON - PROJ'] + inp['D/S SENIOR MVIC']
        mask_gt_795 = np.array(out['RECORD INFLOW'] >= (795 + outflow_adj))
        mvi_storable = np.where(mask_gt_795,
                 795 - out['TOTAL MVI WATER USED'] - exl['SPILL'],
                 out['RECORD INFLOW'] - outflow_adj - out['TOTAL MVI WATER USED'] - exl['SPILL'])
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

        # 2025
        #
        # 2025-05-10 to 2025-06-01
        #    + =(280.641404351437/1.9835)/22
        # 2025-06-01 to 2025-07-01
        #    + =646.095/1.9835/30
        # 2025-07-01 to 2025-08-01
        #    + =1121.512/1.9835/31
        # 2025-08-01 to 2025-09-01
        #    + =('DIST CLASS B'[9]-'DIST CLASS B'[12])/31
        # 2025-09-01 to 2025-10-01
        #    + 0.0
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
    def fill_mvi_narraguinnep_in_mcphee(config, logger, exl, inp, out, custom_data, dates,
                                        water_year_info, narr_in_mcphee_fill_target_af):
        print('\tFill Narraguinnep')
        # Inputs
        spill = exl['SPILL']
        mcphee_daily_evap_af = exl['MCPHEE DAILY EVAP AF']
        mvi_stored_evap = exl['MVI STORED EVAP']
        active_cap = out['ACTIVE CAP']
        num_days = len(active_cap)

        #  Outputs
        out['NARR IN MCP EVAP'] = narr_in_mcphee_evap = WaterYear.output(num_days)
        out['NARR FILL IN MCPHEE'] = narr_fill_in_mcphee = WaterYear.output(num_days)
        out['CUM NARR IN MCP EVAP'] = cum_narr_in_mcphee_evap = WaterYear.output(num_days)
        out['CUM NARR IN MCPHEE'] = cum_narr_in_mcphee = WaterYear.output(num_days)

        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        apr4 = WaterYear.day_for_date(dates, 'Apr-4')
        mar24 = WaterYear.day_for_date(dates, 'Mar-24')
        mar31 = WaterYear.day_for_date(dates, 'Mar-31')
        jul1 = WaterYear.day_for_date(dates, 'Jul-1')

        outflow_adj = exl['MWC NON - PROJ'] + exl['CORTEZ NON - PROJ'] + inp['D/S SENIOR MVIC']
        if water_year_info.year == 2024:
            # Needed to balance 'NARR FILL IN MCPHEE on mar26+, needs research
             outflow_adj[0:apr1] = outflow_adj[0:apr1] - exl['UTE F&R'][0:apr1]
        mask_gt_795 = np.array(out['RECORD INFLOW'] >= (795 + outflow_adj))

        storable = np.where(mask_gt_795,
                 795 - exl['TOTAL MVI WATER USED'],
                 out['RECORD INFLOW'] - outflow_adj - exl['TOTAL MVI WATER USED'] - exl['NARR FILL']  - spill)

        narr_fill_in_mcphee_runs = WaterYear.get_flow_runs(config, logger, 'NARR FILL IN MCPHEE')
        for narr_fill_in_mcphee_run in narr_fill_in_mcphee_runs:
            start_day = WaterYear.day_for_date(dates, narr_fill_in_mcphee_run[0])
            end_day = WaterYear.day_for_date(dates, narr_fill_in_mcphee_run[1])
            for day in range(start_day, end_day+1):
                narr_fill_in_mcphee[day] = storable[day]
        WaterYear.apply_custom_data(custom_data, 'NARR FILL IN MCPHEE', narr_fill_in_mcphee)

        if WaterYear.log_fills:
            WaterYear.log(0, 'CUM NARR IN MCPHEE', f'Start  fill')

        last_fill_day = num_days
        fill_remaining = 0
        fill_complete = False
        fill_runs, drain_runs, evap_runs, custom_runs = WaterYear.get_pool_runs(config, logger, 'CUM NARR IN MCPHEE')
        for day in range(0, num_days):
            # Fill
            #
            if mar24 <= day <= mar31 and DoloresYear.patch_cum_narr_in_mcphee_2025_1:
                # FIXME - Have to subtract 'MWC NON - PROJ' from 'NARR FILL' to get it to verify against DWCD Excel
                # Not sure if they are adding it for a reason, or its a mistake or I subtracted twice, or something
                #
                # IF(exl['RECORD INFLOW'][day]>=795,1
                #   795-MAX(0,exl['DOL TUN TOT DIV'][day]-exl['WET LAND'][day]-exl['SEELEY'][day]-exl['UTE F&R'][day]-exl['MWC NON - PROJ'][day]-exl['CORTEZ NON - PROJ'][day]-exl['CORTEZ PROJ'][day]-exl['UTE PROJ'][day]-exl['F-BAY BAL'][day]+exl['LONE PINE'][day]+exl['U LAT'][day]-exl['TOTTEN (FRESH WATER)'][day]+exl['DIST CLASS B'][day]),
                # storable1 = exl['RECORD INFLOW'][day] - max(0, exl['DOL TUN TOT DIV'][day]-exl['WET LAND'][day]-exl['SEELEY'][day]-exl['UTE F&R'][day]-exl['MWC NON - PROJ'][day]-exl['CORTEZ NON - PROJ'][day]-exl['CORTEZ PROJ'][day]-exl['UTE PROJ'][day]-exl['F-BAY BAL'][day]+exl['LONE PINE'][day]+exl['U LAT'][day]-exl['TOTTEN (FRESH WATER)'][day]+exl['DIST CLASS B'][day] - exl['D/S SENIOR MVIC'][day])-exl['SPILL'][day]
                #
                narr_fill_in_mcphee[day] = narr_fill_in_mcphee[day] + exl['MWC NON - PROJ'][day]

            if not fill_complete:
                if day < apr1:
                    tentative = cum_narr_in_mcphee[day - 1] + narr_fill_in_mcphee[day]
                else:
                    tentative = cum_narr_in_mcphee[day - 1] + storable[day]
                if tentative > narr_in_mcphee_fill_target_af:
                    diff = narr_in_mcphee_fill_target_af - cum_narr_in_mcphee[day - 1]
                    fill_remaining = storable[day] - diff
                    cum_narr_in_mcphee[day] = cum_narr_in_mcphee[day - 1] + diff
                    last_fill_day = day
                    fill_complete = True
                    evap = mvi_stored_evap[day - 1] / WaterYear.af_to_cfs
                    print(f'fill_mvi_narraguinnep_in_mcphee evap {evap} {fill_remaining}')
                else:
                    cum_narr_in_mcphee[day] = tentative
            else:
                cum_narr_in_mcphee[day] = cum_narr_in_mcphee[day-1]

            # Evaporation charge
            jan31 = WaterYear.day_for_date(dates, 'Jan-31')
            if day == jan31:
                pass
            evap = 0
            if not day:
                evap = 0
            elif day <= apr1:
                evap = (mcphee_daily_evap_af[day-1] * ((cum_narr_in_mcphee[day-1] / WaterYear.af_to_cfs)
                                                         / active_cap[day-1]))
                narr_in_mcphee_evap[day-1] = evap * WaterYear.af_to_cfs
                # FIXME - Not sure why this has to be a day behind to verify
                cum_narr_in_mcphee_evap[day-1] = narr_in_mcphee_evap[day-1] + cum_narr_in_mcphee_evap[day-2]
            elif apr1+1 <= day < jul1:
                if DoloresYear.patch_cum_narr_in_mcphee_2025_2 and day == apr4:
                    # This is probably an error in the 2025 inflow/outflow, it seems to be applying evap charges
                    # twice Apr-1 to Apr-33.  Needed to pass verification but should otherwise be removed
                    # Excel comment on CUM NARR IN MCPHEE cell on Apr-4:
                    # Anthony Lee:
                    # NARR water right completed in McPhee midday today. Remaining inflows directed towards Totten Credit.
                    # 20710-9885.7 AF means this column should finish at 5,457.172 CFS-days minus 4.38 AF (2.2CFS)(3 Days) of evaporation = 5454.964 CFS-days total.
                    # The 3 days of evap are deducted in the function.
                    #
                    evap = mvi_stored_evap[day - 1] / 1.9835
                    evap = evap + np.sum(mvi_stored_evap[day-3:day-1]) / 1.9835
                    fill_remaining += evap
                    fill_remaining -= mvi_stored_evap[day - 1] / WaterYear.af_to_cfs
                else:
                    evap = mvi_stored_evap[day-1] / WaterYear.af_to_cfs
                    # FIXME - May need to subtract evap from fill_remaing(last day), above patch is in the way
                    #if fill_remaining:
                    #    fill_remaining -= mvi_stored_evap[day - 1] / WaterYear.af_to_cfs

            if evap:
                cum_narr_in_mcphee[day] = cum_narr_in_mcphee[day] - evap

        if WaterYear.log_fills:
            WaterYear.log(apr4, 'CUM NARR IN MCPHEE', f'Ending fill                   inp {0:7.2f} cfs', is_ending=True)

        return last_fill_day, fill_remaining

    @staticmethod
    def run_mvi_totten_exchange(config, logger, out, x, inp, dates, water_year_info, narr_fill_last_day,
                                 narr_fill_remaining_cfs):
        print('\tFill Totten Exchange')
        to_ex_limit = config.get('TO EX')
        if to_ex_limit is None:
            to_ex_limit = 3400.0 / WaterYear.af_to_cfs
        # FIXME Hack to make 2024 balance
        if DoloresYear.patch_to_ex_2024_1:
            to_ex_limit = 1713.986

        num_days = len(x['MVI STORABLE'])

        day_totten_exchange_fill_ends = 0
        config['day_totten_exchange_fill_ends'] = -1
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        out['TO EX'] = totten_exchange = WaterYear.output(num_days)

        storable = DoloresYear.calc_mvi_storable(x, inp, out, dates, water_year_info)
        mvi_stored_evap = x['MVI STORED EVAP'] / WaterYear.af_to_cfs

        fill_runs, drain_runs, evap_runs, custom_runs = WaterYear.get_pool_runs_as_day_runs(config, logger, 'TO EX', dates)
        if fill_runs:
            fill_run = fill_runs.pop(0)
            evap_run = None
            if evap_runs:
                evap_run = evap_runs.pop(0)

            start_day = fill_run[0]
            if WaterYear.log_fills:
                WaterYear.log(start_day, 'TO EX', f'Start  fill')

            if not narr_fill_last_day:
                narr_fill_last_day = num_days

            for day in range(start_day, oct15+1):
                apr1 = WaterYear.day_for_date(dates, 'Apr-1')
                evap = 0
                if evap_run is not None and day == evap_run[1]:
                    if evap_runs:
                        evap_run = evap_runs.pop(0)
                    else:
                        evap_run = None
                if evap_run is not None:
                    if evap_run[0] <= day < evap_run[1]:
                        evap = mvi_stored_evap[day-1]

                if fill_run is not None and day == fill_run[1]:
                    if fill_runs:
                        fill_run = fill_runs.pop(0)
                    else:
                        fill_run = None
                if fill_run is not None:
                    if fill_run[0] <= day < fill_run[1]:
                        if day == narr_fill_last_day:
                            # FIXME - May need to subtract evap here, not doing it fixes 2025 but it is probably double charging evap on apr-4
                            # totten_exchange[day] = narr_fill_remaining_cfs - evap
                            totten_exchange[day] = narr_fill_remaining_cfs
                        elif storable[day] >= 0:
                            s = storable[day]
                            tentative = totten_exchange[day - 1] + storable[day] - evap
                            if tentative >= to_ex_limit:
                                remaining = tentative - to_ex_limit
                                totten_exchange[day] = to_ex_limit
                                if not day_totten_exchange_fill_ends:
                                    config['fill_remained_cfs'] = totten_exchange[day - 1] - to_ex_limit
                                    config['day_totten_exchange_fill_ends'] = day_totten_exchange_fill_ends = day
                            elif not day_totten_exchange_fill_ends:
                                totten_exchange[day] = tentative
                        elif day > day_totten_exchange_fill_ends:
                            totten_exchange[day] = to_ex_limit
                else:
                    totten_exchange[day] = totten_exchange[day-1] - evap

                if water_year_info.year == 2024:
                    if day == apr1:
                        # FIXME
                        totten_exchange[day] += .063
                    pass

            if WaterYear.log_fills:
                days = day_totten_exchange_fill_ends - narr_fill_last_day
                WaterYear.log(day_totten_exchange_fill_ends, 'TO EX',
                              f'Ending fill                   inp {0:7.2f} cfs {totten_exchange[day_totten_exchange_fill_ends]:7.1f} AF {days:7d} days',
                              is_ending=True)

        return totten_exchange

    @staticmethod
    def fill_mvi_call_water(config, logger, out, exl, inp, comments, dates):
        print('\tCalc MVI Call Water')
        mvi_storable = exl['MVI STORABLE']
        num_days = len(mvi_storable)
        total_mvi_irrigation_water_used = exl['TOTAL MVI IRRIG. WATER USED']
        spill = exl['SPILL']

        variable_names = ['MVI CALL STOR', 'MVI APR- JUNE (DIV+ CALL)', 'MVI CALL SPILLED OR USED']
        WaterYear.comments_for_vars(variable_names, comments, dates)

        out['MVI CALL STOR'] = mvi_call_store = WaterYear.output(num_days)
        out['MVI APR- JUNE (DIV+ CALL)'] = mvi_apr_jun_div_plus_call = WaterYear.output(num_days)
        out['MVI CALL SPILLED OR USED'] = mvi_call_spill_or_used = WaterYear.output(num_days)

        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        jul1 = WaterYear.day_for_date(dates, 'Jul-1')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        day_totten_exchange_fill_ends = WaterYear.get_config(config, '', 'day_totten_exchange_fill_ends')

        # Fill
        #
        if WaterYear.log_fills:
            WaterYear.log(apr1, 'MVI CALL STOR', f'Start  fill                   inp {0:7.2f} cfs')

        partial_call_store = 0
        remainder = 0
        day = 0
        start_day = apr1
        end_day = num_days
        fill_runs, drain_runs, evap_runs, custom_runs = WaterYear.get_pool_runs(config, logger, 'MVI CALL STOR')
        if fill_runs:
            fill_run = fill_runs[0]
            start_day = WaterYear.day_for_date(dates, fill_run[0])
            end_day = WaterYear.day_for_date(dates, fill_run[1])
        day_mvi_call_water_fill_ends = end_day
        call_div = 0
        for day in range(start_day, num_days):
            #if day >= day_totten_exchange_fill_ends:
            storable = mvi_storable[day]
            if day == day_totten_exchange_fill_ends:
                remainder = WaterYear.get_config(config, '', 'fill_remained_cfs')
                storable += remainder

            mvi_call_store[day] = max(0, mvi_call_store[day-1] + storable)

            call_div = (mvi_apr_jun_div_plus_call[day-1] +
                max(0, (total_mvi_irrigation_water_used[day] + storable) * WaterYear.af_to_cfs))
            if day >= jul1:
                break
            elif call_div >= 72000:
                #if day_mvi_call_water_fill_ends == num_days:
                partial_call_store = (72000 - mvi_apr_jun_div_plus_call[day-1]) / WaterYear.af_to_cfs
                # mvi_call_store[day] = mvi_call_store[day] - partial_call_store
                config['day_mvi_call_water_fill_ends'] = day_mvi_call_water_fill_ends = day
                call_div = 72000
                break
            mvi_apr_jun_div_plus_call[day] = call_div
           #  else:
           #      call_div = (mvi_apr_jun_div_plus_call[day-1] +
           #          total_mvi_irrigation_water_used[day] * WaterYear.af_to_cfs)
           #      mvi_apr_jun_div_plus_call[day] = call_div

        for day in range(day_mvi_call_water_fill_ends, num_days):
            mvi_call_store[day] = mvi_call_store[day - 1]

        if WaterYear.log_fills:
            days = day_mvi_call_water_fill_ends - apr1
            WaterYear.log(day_mvi_call_water_fill_ends, 'MVI CALL STOR', f'Ending fill                   inp {remainder:7.2f} cfs {mvi_call_store[day]:7.1f} AF {days:7d} days', is_ending=True)

        # Drain
        #
        if WaterYear.log_drains:
            WaterYear.log(day_mvi_call_water_fill_ends, 'MVI CALL STOR', f'Start  drain                  inp {remainder:7.2f} cfs {mvi_call_store[day]:7.1f} AF')

        last_day = day_mvi_call_water_fill_ends
        drain_complete = False
        for day in range(day_mvi_call_water_fill_ends, num_days):
            if drain_complete:
                mvi_call_store[day] = 0
                continue
            storable = min(0, mvi_storable[day])
            used = total_mvi_irrigation_water_used[day]
            if call_div >= 72000:
                mvi_apr_jun_div_plus_call[day] = 72000
                tentative_drain = mvi_call_store[day-1] - used
            else:
                tentative_drain = mvi_call_store[day-1] + storable
            if tentative_drain >= 0:
                mvi_call_store[day] = tentative_drain
            else:
                used = mvi_call_store[day - 1]
                remainder = -tentative_drain
                mvi_call_store[day] = 0
                drain_complete = True
                last_day = day

            if partial_call_store:
                mvi_call_store[day] = mvi_call_store[day] + partial_call_store
                used -= partial_call_store
                partial_call_store = 0

            mvi_call_spill_or_used[day] = used + spill[day]

        # for day in range(day_mvi_call_water_fill_ends, num_days):
        #    mvi_call_store[day] = mvi_call_store[day - 1]

        if WaterYear.log_drains:
            days = last_day - day_mvi_call_water_fill_ends
            WaterYear.log(last_day, 'MVI CALL STOR', f'Ending drain                  inp {remainder:7.2f} cfs {mvi_call_store[day]:7.1f} AF {days:7d} days', is_ending=True)

        # "Fill" project water
        #
        fill_runs, drain_runs, evap_runs, custom_runs = WaterYear.get_pool_runs(config, logger, 'MVI PROJ')
        mvi_proj_af = WaterYear.get_config(config, '', 'MVI PROJ')
        out['MVI PROJ'] = WaterYear.output(num_days)
        out['MVI PROJ'][jul1:oct15] = mvi_proj_af / WaterYear.af_to_cfs

        return last_day, remainder

    @staticmethod
    def fill_mvi_upstream_exchange(config, logger, out, inp, dates):
        ground_hog_discharge = inp['GRNDHOG DISCHARGE']
        num_days  = len(ground_hog_discharge)

        out['U/S EX'] = pool_cfs = WaterYear.output(num_days)
        out['U/S USERS EXCH'] = us_exchange_cfs =  WaterYear.output(num_days)

        param_upstream_exchange_cfs = WaterYear.get_config(config, '', 'U/S USERS EXCH')
        remaining_cfs = param_upstream_exchange_cfs / WaterYear.af_to_cfs
        last_day = 0
        fill_left_cfs = 0
        first_day = 0
        full = config.get('U/S USERS EXCH') / WaterYear.af_to_cfs

        mvi_upstream_exchange_runs = WaterYear.get_flow_runs(config, logger, 'U/S USERS EXCH')
        fill_runs, drain_runs, fills_runs, custom_runs = WaterYear.get_pool_runs(config, logger, 'U/S EX')

        if WaterYear.log_fills and mvi_upstream_exchange_runs:
            start_day =  WaterYear.day_for_date(dates, mvi_upstream_exchange_runs[0][0])
            first_flow = out['U/S USERS EXCH'][last_day]
            WaterYear.log(start_day, 'U/S EX', f'Start  fill                       {first_flow:7.2f} cfs')

        tolerance = 1e-6
        total_fill = 0
        fill_complete = False
        fill_last_day = num_days
        for n, mvi_upstream_exchange_run in enumerate(mvi_upstream_exchange_runs):
            start_date = mvi_upstream_exchange_run[0]
            first_day = start_day = WaterYear.day_for_date(dates, start_date)
            param_cfs = mvi_upstream_exchange_run[2]
            if n < len(mvi_upstream_exchange_runs)-1:
                end_date = mvi_upstream_exchange_run[1]
                end_day = WaterYear.day_for_date(dates, end_date)
            else:
                end_day = WaterYear.day_for_date(dates, 'Oct-15')

            for day in range(start_day, end_day+1):
                if not fill_complete:
                    fill_cfs = param_cfs
                else:
                    fill_cfs = 0
                if fill_cfs > ground_hog_discharge[day]:
                    fill_cfs = ground_hog_discharge[day]
                if fill_cfs >= remaining_cfs:
                    fill_left_cfs = fill_cfs - remaining_cfs
                    fill_cfs = remaining_cfs
                remaining_cfs -= fill_cfs
                us_exchange_cfs[day] = fill_cfs
                pool_cfs[day] = pool_cfs[day - 1] + fill_cfs
                total_fill += fill_cfs
                print(f'U/S EX {dates[day]} {total_fill} {pool_cfs[day]} {fill_cfs} {ground_hog_discharge[day]}')
                if not fill_complete and (total_fill >= full or np.isclose(total_fill, full, atol=tolerance)):
                    # Its not unexpected that the fill will end before this triggers, it often comes up a little short of 'full'
                    # A product of the tech computing 'U/S USER EXCH' downing to a nearly exact floating point number
                    print(f'Upstream exchange fill complete {total_fill} {pool_cfs[day]}')
                    fill_complete = True
                    last_day = day
                # if remaining_cfs <= 0 or fill_cfs == 0:
                #     pool_cfs[day] = 0
                #     last_day = day
                #     break
        if WaterYear.log_fills:
            if last_day:
                days = last_day - first_day
                pool_af = out['U/S EX'][last_day] * WaterYear.af_to_cfs
                last_flow = out['U/S USERS EXCH'][last_day]
                WaterYear.log(last_day, 'U/S EX',
                              f'Ending fill                       {last_flow:7.2f} cfs {pool_af:7.1f} AF {days:7d} days', is_ending=True)

        return last_day, fill_left_cfs

    @staticmethod
    def run_spill_runs(config, logger, exl, out, custom_data, dates):
        below_mcp = exl['BELOW MCP']
        num_days  = len(below_mcp)

        spill = out['SPILL'] = WaterYear.output(num_days)
        spill_runs = WaterYear.get_flow_runs(config, logger, 'SPILL')
        for spill_run in spill_runs:
            start_day = WaterYear.day_for_date(dates, spill_run[0])
            end_day = WaterYear.day_for_date(dates, spill_run[1])
            for day in range(start_day, end_day + 1):
                spill[day] = tmp = below_mcp[day]

        WaterYear.apply_custom_data(custom_data, 'SPILL', spill)

        return spill

    @staticmethod
    def calc_fish_pool_left(config, logger, exl, inp, dates, water_year_info):
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
        if ufr_class_a_shares_af is not None:
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
    def calc_tunnel_flows(inp, out, dates):
        num_days = len(dates)
        out['CORTEZ NON - PROJ'] = WaterYear.output(num_days)
        out['CORTEZ PROJ'] = WaterYear.output(num_days)

        apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        sep1 = WaterYear.day_for_date(dates, 'Sep-1')
        oct1 = WaterYear.day_for_date(dates, 'Oct-1')

        # Ute Farm and Ranch, this is synonymous with DWR CDSS Towaoc canal flow, with 1.05 adustment removed
        out['UTE F&R'] = inp['UTE F&R CFS'] * 1.05

        # Montezuma Water Company project water
        #
        result = (inp['MWC NON - PROJ CFS']) * 1.02
        out['MWC NON - PROJ'] = result

        # Ute Project water, I think this is Towaoc Domestic water via Cortez treatment plant
        #
        result = (inp['UTE PROJ CFS'] * 1.06) * 1.04
        out['UTE PROJ'] = result

        # City of Cortez Non Project water
        result = (inp['CORTEZ NON - PROJ CFS'] * 1.04) - out['UTE PROJ']
        if DoloresYear.patch_cortez_non_proj_2025_1:
            # FIXME - this changed from 1.04 to 1.02, 1.02 is the MWC factor, and is using gallons instead of the standard formula
            result[sep1:oct1] = inp['CORTEZ NON - PROJ CFS'][sep1:oct1] * 1.02
        result = np.maximum(result, 0)
        result[result > 4.2] = 4.2
        out['CORTEZ NON - PROJ'] = result

        # City of Cortez Project water
        # 'CORTEZ PROJ'
        result = (inp['CORTEZ PROJ CFS'] * 1.04) - out['UTE PROJ']
        result[apr1:] = result[apr1:] - 4.2
        result[apr1:] = np.maximum(result[apr1:], 0)
        result[result > 4.2] = 4.2
        out['CORTEZ PROJ'] = result

    @staticmethod
    def calc_dwcd(config, logger, out, exl, inp, dates):
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
            floor = 795 + exl['MWC NON - PROJ'][day] + exl['CORTEZ NON - PROJ'][day] + inp['D/S SENIOR MVIC'][day] + inp['D/S SENIOR PROJ'][day]
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
    def drain_mvi_pool(variable_name, out, dates, storable_cfs, start_day, last_remaining):
        pool_cfs = out[variable_name]
        if start_day < len(pool_cfs):
            pool_af = pool_cfs[start_day] * WaterYear.af_to_cfs
            print(f'\tDraining {variable_name} {pool_af} af  Remaining cfs from previous drain: {last_remaining}')
        else:
            return start_day, last_remaining

        num_days = len(pool_cfs)
        if WaterYear.log_drains:
            WaterYear.log(start_day, variable_name, f'Start  drain                  inp {last_remaining:7.2f} cfs {pool_af:7.1f} AF')
        oct15 = WaterYear.day_for_date(dates, 'Oct-15')

        # Upstream exchange can fill and drain at the same time, this preserves the fill
        fills = DoloresYear.cumulative_fill_after_day(pool_cfs, start_day)

        remaining = 0
        last_day = None
        for day in range(start_day, num_days):
            if day > oct15:
                pool_cfs[day] = 0.0
                last_day = oct15+1
                continue
            if last_remaining:
                # If previous pool finished draining and satisfied some of the daily drain
                # we just finish draining what was left over from that drain first time through
                drain = last_remaining
                last_remaining = 0
            else:
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
                    break
            else:
                # MVI isn't using water so just propagate last value
                pool_cfs[day] = pool

        if last_day:
            for day in range(last_day, num_days):
                pool_cfs[day] = 0.0

        if last_day:
            pool_af = pool_cfs[last_day] * WaterYear.af_to_cfs
            if WaterYear.log_drains:
                WaterYear.log(last_day, variable_name, f'Ending drain                  out {remaining:7.2f} cfs {pool_af:7.1f} AF {last_day-start_day:7d} days', is_ending=True)
        else:
            pool_af = pool_cfs[num_days-1] * WaterYear.af_to_cfs
            no_remainder = ' '
            continue_day = num_days-1-start_day
            if WaterYear.log_drains:
                WaterYear.log(num_days-1, variable_name, f'Draining                        {no_remainder:7}     {pool_af:7.1f} AF {continue_day:7d} days', is_ending=True)

        return last_day, -remaining



