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
from source.water_year_info import WaterYearInfo
from api.event_log import EventLog
from api.ui_abstraction import UIAbstraction
from dwcd.water_year import WaterYear
from api.pool import Pool, PoolQueue, DrainRun, DrainType, FillRun, FillType


class NarrInMcpheePool(Pool):
    def __init__(self, pool_name:str, owner_name:str, exl:dict, inp:dict, out:dict, dates,
                 water_year_info:WaterYearInfo, pool_queue_all:PoolQueue, narr_fill_in_mcphee_runs,
                 custom_data, storable):
        super().__init__(pool_name, owner_name)

        self.pool_queue_all = pool_queue_all
        self.pool_queue = self.pool_queue_all.get_runs_for_variable_name('CUM NARR IN MCPHEE')

        # Set fill target, need to decide where and how to do this
        #
        if water_year_info.year == 2025:
            # self.fill_target_af = 5457.172 # Target without the 2025_1 evap patch below
            self.fill_target_cfs = 5454.964  # Target with the 2025_1 evap patch below
            self.fill_target_min_day = WaterYear.day_for_date(dates, 'Mar-31')
        elif water_year_info.year == 2024:
            # First fill peaked Mar-24
            # Second actual fill complete Jun-10
            self.fill_target_cfs = 1902.570
            self.fill_target_min_day = WaterYear.day_for_date(dates, 'Jun-09')
        elif 'NARR FILL IN MCPHEE' in exl:
            narr_fill_in_mcphee = exl['NARR FILL IN MCPHEE']
            narr_fill_in_mcphee_sum = np.sum(narr_fill_in_mcphee) * WaterYear.af_to_cfs
            self.fill_target_cfs = narr_fill_in_mcphee_sum
            self.fill_target_min_day = 0
        else:
            print(f'narr_fill_in_mcphee_target not set')
            return

        # Inputs
        #
        self.spill = exl['SPILL']
        self.mcphee_daily_evap_af = exl['MCPHEE DAILY EVAP AF']
        if 'MVI EVAP' in out:
            self.mvi_evap = out['MVI EVAP']
        else:
            self.mvi_evap = exl['MVI STORED EVAP']
        self.active_cap = out['ACTIVE CAP']
        num_days = len(self.active_cap)

        self.apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        self.storable = storable.copy() - exl['NARR FILL']
        if water_year_info.year == 2023:
            # Not sure why UF&R is drawing so much water in 2023
            # For some reason can't subtract UTE F&R on Nov-16 without verification error
            nov15 = WaterYear.day_for_date(dates, 'Nov-15')
            self.storable[:nov15] = self.storable[:nov15] + exl['UTE F&R'][:nov15]
            jan23 = WaterYear.day_for_date(dates, 'Jan-23')
            mar28 = WaterYear.day_for_date(dates, 'Mar-28')
            self.storable[jan23:mar28] = self.storable[jan23:mar28] + exl['UTE F&R'][jan23:mar28]

        #  Outputs
        #
        out['NARR IN MCP EVAP'] = self.narr_in_mcphee_evap = WaterYear.output(num_days)
        out['NARR FILL IN MCPHEE'] = self.narr_fill_in_mcphee = WaterYear.output(num_days)
        out['CUM NARR IN MCP EVAP'] = self.cum_narr_in_mcphee_evap = WaterYear.output(num_days)
        out['CUM NARR IN MCPHEE'] = self.pool = WaterYear.output(num_days)

        # Build 'NARR FILL IN MCPHEE', its special
        # FIXME - Needs to be done daily, or something, custom data is a problem
        #
        self.mar24 = WaterYear.day_for_date(dates, 'Mar-24')
        self.mar31 = WaterYear.day_for_date(dates, 'Mar-31')
        if narr_fill_in_mcphee_runs is not None:
            for narr_fill_in_mcphee_run in narr_fill_in_mcphee_runs:
                start_day = WaterYear.day_for_date(dates, narr_fill_in_mcphee_run[0])
                end_day = WaterYear.day_for_date(dates, narr_fill_in_mcphee_run[1])
                for day in range(start_day, end_day + 1):
                    self.narr_fill_in_mcphee[day] = self.storable[day]
                    if self.mar24 <= day <= self.mar31 and water_year_info.year == 2025:
                        # FIXME - Have to subtract 'MWC' from 'NARR FILL' to get it to verify against DWCD Excel
                        # Not sure if they are adding it for a reason, or its a mistake or I subtracted twice, or something
                        #
                        self.narr_fill_in_mcphee[day] = self.narr_fill_in_mcphee[day] + exl['MWC'][day]
            WaterYear.apply_custom_data(custom_data, 'NARR FILL IN MCPHEE', self.narr_fill_in_mcphee)

        self.fill_complete = False
        self.oct15 = WaterYear.day_for_date(dates, 'Oct-15')

    def daily_update(self, day:int, date_str:str, pool_queue:PoolQueue, logger:UIAbstraction, event_log:EventLog,
                     exl:dict, inp:dict, out:dict, custom_data:dict, dates:list, water_year_info:WaterYearInfo):

        if day > self.oct15:
            return
        date_str = WaterYearInfo.format_to_month_day(dates[day])
        if date_str == 'May-09':
            pass
        fill_run, drain_run, evap_run = pool_queue.get_runs_for_day(day, 'CUM NARR IN MCPHEE')

        evap = 0
        if evap_run is not None:
            if day == 0:
                evap = 0
            elif day < self.apr1:
                # evap = narr_in_mcphee_evap[day - 1] / WaterYear.af_to_cfs
                evap = self.mvi_evap[day - 1] / WaterYear.af_to_cfs
            else:
                evap = self.mvi_evap[day - 1] / WaterYear.af_to_cfs
        if water_year_info.year == 2025 and day == self.apr1 + 3:
            # This is probably an error in the 2025 inflow/outflow, it seems to be applying evap charges
            # twice Apr-1 to Apr-3.  Needed to pass verification but should otherwise be removed
            # Excel comment on CUM NARR IN MCPHEE cell on Apr-4:
            # Anthony Lee:
            # NARR water right completed in McPhee midday today. Remaining inflows directed towards Totten Credit.
            # 20710-9885.7 AF means this column should finish at 5,457.172 CFS-days minus 4.38 AF (2.2CFS)(3 Days) of evaporation = 5454.964 CFS-days total.
            # The 3 days of evap are deducted in the function.
            #
            self.mvi_evap[day - 1] = (self.mvi_evap[day - 1] + np.sum(self.mvi_evap[day - 3:day - 1])) / WaterYear.af_to_cfs
            # evap = evap + t

        tentative = 0
        if fill_run is not None:
            if day > 0 and day == fill_run.start_day:
                end_runs: list[FillRun] = self.pool_queue_all.get_completed_on_day(fill_run.start_day)
                if end_runs:
                    tentative = end_runs[0].complete_remaining_cfs
                    self.pool[day] = self.pool[day - 1] + tentative - evap
                    self.daily_evap(day)
                    return

            if fill_run.fill_type == FillType.PAPER_FILL:
                n = day - fill_run.start_day
                if n < len(fill_run.paper_fills):
                    tentative = fill_run.paper_fills[n]
                else:
                    tentative = self.storable[day]
            elif self.narr_fill_in_mcphee[day] >= 0:
                tentative = self.storable[day] - evap
            else:
                tentative = 0
            if self.mar24 <= day <= self.mar31 and water_year_info.year == 2025:
                # FIXME - Have to subtract 'MWC' from 'NARR FILL' to get it to verify against DWCD Excel
                # Not sure if they are adding it for a reason, or its a mistake or I subtracted twice, or something
                #
                tentative = tentative + exl['MWC'][day]
        elif drain_run is not None:
            if drain_run.drain_type == DrainType.PAPER_DRAIN or drain_run.drain_type == DrainType.TRANSFER:
                n = day - drain_run.start_day
                if n < len(drain_run.paper_drains):
                    tentative = drain_run.paper_drains[n]  # Evap is probably lumped in with the paper transfer
                else:
                    print(f'fill_mvi_narraguinnep paper fill short of values {date_str}')
                    tentative = -evap
            else:
                tentative = self.storable[day] - evap

        if tentative > 0 and not self.fill_complete:
            t = self.pool[day - 1] + tentative
            if self.fill_target_cfs and t >= self.fill_target_cfs and day > self.fill_target_min_day:
                self.pool[day] = self.fill_target_cfs
                diff = self.pool[day] - self.pool[day - 1]
                fill_remaining = self.storable[day] - diff - evap
                fill_run.ending(logger, day, fill_remaining)
                self.fill_complete = True
            else:
                self.pool[day] = self.pool[day - 1] + tentative
        elif tentative < 0:
            if -tentative > self.pool[day - 1] and not drain_run.overdrafts:
                self.pool[day] = 0
                drain_remaining = -tentative - self.pool[day - 1]
                drain_run.ending(logger, day, drain_remaining)
            else:
                self.pool[day] = self.pool[day - 1] + tentative
        else:
            self.pool[day] = self.pool[day - 1] - evap

        # if water_year_info.year == 2024 and day == apr1:
        #    cum_narr_in_mcphee_evap[day - 1] = narr_in_mcphee_evap[day - 1] + cum_narr_in_mcphee_evap[day - 2]
        #    evap_today = (mcphee_daily_evap_af[day - 1] * ((pool[day - 1] / WaterYear.af_to_cfs)
        #                                                   / active_cap[day - 1]))
        #    narr_in_mcphee_evap[day - 1] = evap_today * WaterYear.af_to_cfs
        if evap_run is not None or (water_year_info.year == 2025 and 8 < day < 14):
            if day >= self.apr1:
                pass
            else:
                self.daily_evap(day)

    def daily_evap(self, day:int):
        evap_today = (self.mcphee_daily_evap_af[day] * (
                (self.pool[day] / WaterYear.af_to_cfs) / self.active_cap[day]))
        self.narr_in_mcphee_evap[day] = evap_today * WaterYear.af_to_cfs
        self.cum_narr_in_mcphee_evap[day] = self.narr_in_mcphee_evap[day] + self.cum_narr_in_mcphee_evap[day - 1]

class TottenExchangePool(Pool):
    def __init__(self, pool_name:str, owner_name:str, config:dict, exl:dict, out:dict, dates,
                 water_year_info:WaterYearInfo, pool_queue_all:PoolQueue, storable):
        super().__init__(pool_name, owner_name)

        self.pool_queue_all = pool_queue_all
        self.pool_queue = self.pool_queue_all.get_runs_for_variable_name('TO EX')

        self.to_ex_limit = config.get('TO EX')
        if self.to_ex_limit is None:
            self.to_ex_limit = 3400.0 / WaterYear.af_to_cfs

        # Inputs
        self.storable = storable
        if 'MVI EVAP' in out:
            self.mvi_evap = out['MVI EVAP']
        else:
            self.mvi_evap = exl['MVI STORED EVAP']
        num_days = len(self.mvi_evap)

        #  Outputs
        self.pool = WaterYear.get_out('TO EX', out, num_days)

        self.day_totten_exchange_fill_ends = 0
        self.oct15 = WaterYear.day_for_date(dates, 'Oct-15')


    def daily_update(self, day:int, date_str:str, pool_queue:PoolQueue, logger:UIAbstraction, event_log:EventLog,
                     exl:dict, inp:dict, out:dict, custom_data:dict, dates:list, water_year_info:WaterYearInfo):

        if day > self.oct15:
            return

        date_str = WaterYearInfo.format_to_month_day(dates[day])
        if date_str == 'Jul-23':
            pass

        fill_run, drain_run, evap_run = self.pool_queue.get_runs_for_day(day, 'TO EX')

        evap = 0
        if evap_run is not None:
            evap = self.mvi_evap[day - 1] / WaterYear.af_to_cfs

        if fill_run is not None:
            if day == fill_run.start_day:
                end_runs: list[FillRun] = self.pool_queue_all.get_completed_on_day(fill_run.start_day)
                if end_runs:
                    tentative = end_runs[0].complete_remaining_cfs
                    self.pool[day] = self.pool[day - 1] + tentative # FIXME may need to subtract evap here but it breaks 2025
                    return

            if fill_run.fill_type == FillType.PAPER_FILL:
                n = day - fill_run.start_day
                if n < len(fill_run.paper_fills):
                    tentative = fill_run.paper_fills[n]
                else:
                    tentative = 0 - evap
            else:
                tentative = self.storable[day] - evap

            if self.pool[day - 1] + tentative >= self.to_ex_limit:
                self.pool[day] = self.to_ex_limit
                remaining = self.storable[day] - (self.pool[day] - self.pool[day - 1])
                fill_run.ending(logger, day, remaining)
            elif self.day_totten_exchange_fill_ends:
                self.pool[day] = self.pool[day - 1]
            else:
                self.pool[day] = self.pool[day - 1] + tentative

        elif drain_run is not None:
            if day == drain_run.start_day:
                end_runs: list[DrainRun] = self.pool_queue_all.get_completed_on_day(drain_run.start_day)
                if end_runs:
                    # self.pool[day - 1] = t = self.pool[day - 2] - end_runs[0].complete_remaining_cfs
                    pass
            if drain_run.drain_type == DrainType.PAPER_DRAIN or drain_run.drain_type == DrainType.TRANSFER:
                n = day - drain_run.start_day
                if n < len(drain_run.paper_drains):
                    tentative = drain_run.paper_drains[n] - evap
                else:
                    print('fill TO EX paper fill short of values')
                    tentative = -evap
            else:
                tentative = -self.storable[day] + evap
            if tentative < self.pool[day - 1]:
                self.pool[day] = self.pool[day - 1] - tentative
            else:
                if not drain_run.complete_day:
                    remaining = self.pool[day-1] - tentative
                    drain_run.ending(logger, day, remaining)
                self.pool[day] = 0
        else:
            self.pool[day] = self.pool[day - 1] - evap


class CallWaterPool(Pool):
    def __init__(self, pool_name:str, owner_name:str, exl:dict, out:dict, dates, pool_queue_all:PoolQueue):
        super().__init__(pool_name, owner_name)

        self.pool_queue_all = pool_queue_all
        self.pool_queue = self.pool_queue_all.get_runs_for_variable_name('MVI CALL STOR')

        # fill_target = 90000
        self.fill_target = 72000

        # Inputs
        self.storable = exl['MVI STORABLE']
        if 'MVI EVAP' in out:
            self.mvi_evap = out['MVI EVAP']
        else:
            self.mvi_evap = exl['MVI STORED EVAP']
        num_days = len(self.storable)
        if 'MVI TOTAL IRRIG' in exl:
            self.mvi_total_irrigation = exl['MVI TOTAL IRRIG']
        else:
            self.mvi_total_irrigation = exl['MVI TOTAL WATER USED']
        self.spill = exl['SPILL']
        self.record_inflow = exl['RECORD INFLOW']
        self.downstream_mvic_senior = exl['D/S SENIOR MVIC']
        self.x = exl

        # Outputs
        self.pool = WaterYear.get_out('MVI CALL STOR', out, num_days)
        out['MVI APR- JUNE (DIV+ CALL)'] = self.mvi_apr_jun_div_plus_call = WaterYear.output(num_days)
        out['MVI CALL SPILLED OR USED'] = self.mvi_call_spill_or_used = WaterYear.output(num_days)

        self.apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        self.jul1 = WaterYear.day_for_date(dates, 'Jul-1')
        self.oct15 = WaterYear.day_for_date(dates, 'Oct-15')
        self.call_water_is_filling = True

    def daily_update(self, day:int, date_str:str, pool_queue:PoolQueue, logger:UIAbstraction, event_log:EventLog,
                     exl:dict, inp:dict, out:dict, custom_data:dict, dates:list, water_year_info:WaterYearInfo):

        partial_call_store = 0
        if day < self.apr1 or day > self.oct15:
            return

        date_str = WaterYearInfo.format_to_month_day(dates[day])
        if date_str == 'May-08':
            pass

        fill_run, drain_run, evap_run = pool_queue.get_runs_for_day(day, 'MVI CALL STOR')

        evap = 0
        if evap_run is not None:
            evap = self.mvi_evap[day - 1] / WaterYear.af_to_cfs

        if fill_run is None and drain_run is None:
            if self.call_water_is_filling:
                if day < self.jul1:
                    tentative = 0
                    self.mvi_apr_jun_div_plus_call[day] = (self.mvi_apr_jun_div_plus_call[day - 1] +
                                                      (self.mvi_total_irrigation[day] + tentative) * WaterYear.af_to_cfs)
            self.pool[day] = self.pool[day - 1] - evap
        else:
            if drain_run and self.spill[day] > 0:
                # NVU CALL STOR Jul-01
                # =x['MVI CALL STOR'][day-3]+MIN(0,x['MVI STORABLE'][day])-x['SPILL'][day]
                # 'MVI APR- JUNE (DIV+ CALL)'
                # =x['MVI APR- JUNE (DIV+ CALL)'][day-1]+(((x['MVI TOTAL IRRIG'][day]-x['NARR FILL'][day])+(x['MVI CALL STOR'][day]-x['MVI CALL STOR'][day-1]))*1.9835)
                #
                # MVI CALL SPILLED OR USED
                #   =MAX(0,IF((
                #       IF(x['RECORD INFLOW'][day]>=795,
                #           795-x['MVI TOTAL WATER USED'][day],
                #   x['RECORD INFLOW'][day]-x['MWC'][day]-x['CORTEZ NON - PROJ'][day]-x['MVI TOTAL WATER USED'][day]-x['D/S SENIOR MVIC'][day]))
                #       <=x['SPILL'][day],
                #   (IF(x['RECORD INFLOW'][day]>=795,
                #     795-x['MVI TOTAL WATER USED'][day],
                #     x['RECORD INFLOW'][day]-x['MWC'][day]-x['CORTEZ NON - PROJ'][day]-x['MVI TOTAL WATER USED'][day]-x['D/S SENIOR MVIC'][day])),
                #     x['SPILL'][day]))
                #
                if day >= self.jul1:
                    self.pool[day] = max(0, self.pool[day-1] + min(0, self.storable[day]) - self.spill[day])
                    if water_year_info.year == 2023 and date_str == 'Jul-03':
                        self.mvi_call_spill_or_used[day] = self.pool[day-1]
                    else:
                        self.mvi_call_spill_or_used[day] = self.spill[day]
                else:
                    tentative = -self.storable[day]
                    self.pool[day] = max(0, self.pool[day - 1] - tentative)
                    if water_year_info.year == 2023 and date_str=='Apr-30':
                        used = self.mvi_total_irrigation[day]
                        self.mvi_call_spill_or_used[day] = 795 - used - self.downstream_mvic_senior[day]
                    elif water_year_info.year == 2023 and date_str == 'May-08':
                        self.mvi_call_spill_or_used[day] = self.pool[day-1]  # Pool is drained
                    else:
                        self.mvi_call_spill_or_used[day] = tentative
                    call_div = (self.mvi_apr_jun_div_plus_call[day - 1] +
                                (self.mvi_total_irrigation[day] - tentative) * WaterYear.af_to_cfs)
                    if water_year_info.year == 2023 and date_str == 'May-08':
                        # pool iw drained in 2023
                        used = self.mvi_total_irrigation[day]
                        j = (used + self.pool[day] - self.pool[day-1]) * WaterYear.af_to_cfs
                        self.mvi_apr_jun_div_plus_call[day] = self.mvi_apr_jun_div_plus_call[day-1] + j
                    else:
                        self.mvi_apr_jun_div_plus_call[day] = call_div
            elif self.call_water_is_filling:
                if fill_run is not None:
                    if day == fill_run.start_day:
                        end_runs: list[FillRun] = self.pool_queue_all.get_completed_on_day(fill_run.start_day)
                        if end_runs:
                            tentative = end_runs[0].complete_remaining_cfs
                        elif fill_run.paper_start_cfs:
                            tentative = fill_run.paper_start_cfs
                        else:
                            tentative = self.storable[day] - evap
                    elif fill_run.fill_type == FillType.PAPER_FILL:
                        n = day - fill_run.start_day
                        if n < len(fill_run.paper_fills):
                            tentative = fill_run.paper_fills[n] - evap
                        else:
                            tentative = self.storable[day] - evap
                    else:
                        tentative = self.storable[day] - evap
                else:
                    tentative = self.storable[day] - evap

                call_div = (self.mvi_apr_jun_div_plus_call[day - 1] +
                            (self.mvi_total_irrigation[day] + tentative) * WaterYear.af_to_cfs)
                if day >= self.jul1:
                    call_div = 0
                    self.pool[day] = self.pool[day - 1] + tentative
                elif call_div >= self.fill_target:
                    self.call_water_is_filling = False
                    partial_call_store = (self.fill_target - self.mvi_apr_jun_div_plus_call[
                        day - 1]) / WaterYear.af_to_cfs
                    self.pool[day] = self.pool[day - 1] - partial_call_store
                    month_day = WaterYearInfo.format_to_month_day(dates[day])
                    logger.log_message(
                        f'  {month_day} MVI Call Water fill complete: {partial_call_store:6.2f} CFS')

                    call_div = self.fill_target
                else:
                    self.pool[day] = self.pool[day - 1] + tentative
                self.mvi_apr_jun_div_plus_call[day] = call_div

                if self.spill[day] > 0:
                    tentative = self.spill[day]
                    if  self.spill[day] > self.pool[day-1]:
                        tentative = self.pool[day-1]
                    self.mvi_call_spill_or_used[day] = tentative

            if drain_run is not None and not self.call_water_is_filling:
                if day == drain_run.start_day:
                    end_runs: list[DrainRun] = self.pool_queue_all.get_completed_on_day(drain_run.start_day)
                    if end_runs:
                        self.pool[day - 1] = self.pool[day - 2] - end_runs[0].complete_remaining_cfs
                if drain_run.drain_type == DrainType.PAPER_DRAIN or drain_run.drain_type == DrainType.TRANSFER:
                    n = day - drain_run.start_day
                    if n < len(drain_run.paper_drains):
                        tentative = -drain_run.paper_drains[n] - evap
                    else:
                        print('fill TO EX paper fill short of values')
                        tentative = -evap
                else:
                    storable_min = min(0, self.storable[day])
                    if day < self.jul1:
                        used = self.mvi_total_irrigation[day]
                        self.mvi_apr_jun_div_plus_call[day] = 72000
                    else:
                        used = 0 - storable_min + self.spill[day]
                    tentative = used - evap
                if partial_call_store:
                    self.pool[day] = self.pool[day] + partial_call_store
                    tentative -= partial_call_store
                if tentative < self.pool[day - 1]:
                    self.pool[day] = self.pool[day - 1] - tentative
                    self.mvi_call_spill_or_used[day] = tentative + self.spill[day]
                else:
                    if not drain_run.complete_day:
                        remaining = self.storable[day] + self.pool[day - 1]
                        self.mvi_call_spill_or_used[day] = self.pool[day - 1]
                        drain_run.ending(logger, day, remaining)
                    self.pool[day] = 0


class UpstreamExchangePool(Pool):
    def __init__(self, pool_name:str, owner_name:str, config:dict, exl:dict, inp:dict, out:dict, dates,
                 water_year_info:WaterYearInfo, pool_queue_all:PoolQueue):
        super().__init__(pool_name, owner_name)

        self.pool_queue_all = pool_queue_all
        self.pool_queue = self.pool_queue_all.get_runs_for_variable_name('U/S EX')

        # Inputs
        #
        self.storable = exl['MVI STORABLE']
        if 'MVI EVAP' in out:
            self.mvi_evap = out['MVI EVAP']
        else:
            self.mvi_evap = exl['MVI STORED EVAP']
        if water_year_info.year >= 2014:
            self.ground_hog_discharge = inp['GRNDHOG DISCHARGE']
        else:
            self.ground_hog_discharge = None
        num_days = len(self.mvi_evap)

        # Outputs
        #
        out['U/S USERS EXCH'] = self.us_exchange_cfs = WaterYear.output(num_days)
        out['U/S EX'] = self.pool = WaterYear.output(num_days)

        param_upstream_exchange_cfs = WaterYear.get_config(config, '', 'U/S USERS EXCH')
        self.remaining_cfs = param_upstream_exchange_cfs / WaterYear.af_to_cfs

        full_af = config.get('U/S USERS EXCH')
        if full_af is not None:
            self.full_cfs = full_af / WaterYear.af_to_cfs
        else:
            self.full_cfs = 0

        self.total_fill = 0
        self.fill_complete = False
        self.apr1 = WaterYear.day_for_date(dates, 'Apr-1')

    def daily_update(self, day:int, date_str:str, pool_queue:PoolQueue, logger:UIAbstraction, event_log:EventLog,
                     exl:dict, inp:dict, out:dict, custom_data:dict, dates:list, water_year_info:WaterYearInfo):
        tolerance = 1e-6

        if day < self.apr1:
            return
        date_str = WaterYearInfo.format_to_month_day(dates[day])
        if date_str == 'Sep-02':
            pass

        fill_run, drain_run, evap_run = pool_queue.get_runs_for_day(day, 'U/S EX')

        evap = 0
        if evap_run is not None:
            evap = self.mvi_evap[day - 1] / WaterYear.af_to_cfs

        if fill_run is None and drain_run is None:
            self.pool[day] = self.pool[day - 1]
        else:
            if fill_run is not None:
                param_cfs = fill_run.get_value_for_day(day)
                if not self.fill_complete:
                    fill_cfs = param_cfs
                else:
                    fill_cfs = 0
                if water_year_info.year >= 2014:
                    if fill_cfs > self.ground_hog_discharge[day]:
                        fill_cfs = self.ground_hog_discharge[day]
                if fill_cfs >= self.remaining_cfs:
                    fill_cfs = self.remaining_cfs
                self.remaining_cfs -= fill_cfs
                self.us_exchange_cfs[day] = fill_cfs
                self.pool[day] = self.pool[day - 1] + fill_cfs
                self.total_fill += fill_cfs
                # print(f'U/S EX {dates[day]} {total_fill} {pool_cfs[day]} {fill_cfs} {ground_hog_discharge[day]}')
                if not self.fill_complete and (self.total_fill >= self.full_cfs or np.isclose(self.total_fill, self.full_cfs, atol=tolerance)):
                    # It's not unexpected that the fill will end before this triggers, it often comes up a little short of 'full'
                    # A product of the tech computing 'U/S USER EXCH' downing to a nearly exact floating point number
                    # print(f'Upstream exchange fill complete {total_fill} {pool_cfs[day]}')
                    self.fill_complete = True

                    # Upstream exchange doesn't use storable, don't want the end of this
                    # mixed in with and confusing fills and drains that do use storable
                    # fill_run.ending(logger, day, remaining_cfs)

            if drain_run is not None:
                if day == drain_run.start_day:
                    end_runs: list[DrainRun] = self.pool_queue_all.get_completed_on_day(drain_run.start_day)
                    if end_runs:
                        for end_run in end_runs:
                            if isinstance(end_run, DrainRun):
                                if end_run.drain_type == DrainType.PAPER_DRAIN:
                                    # FIXME - This pretty much a hack to match what DWCD did in 2025
                                    # =IF(x['U/S USERS EXCH'][day]="",x['U/S EX'][day-1],x['U/S EX'][day-1]+x['U/S USERS EXCH'][day])+(x['MVI STORABLE'][day]+x['CUM NARR IN MCPHEE'][day-1])
                                    # n = exl['CUM NARR IN MCPHEE'][day - 1]
                                    # s = self.storable[day]
                                    self.pool[day] = self.pool[day] + self.storable[day] - end_run.paper_drains[-1]
                                else:
                                    self.pool[day] = self.pool[day - 1] + end_run.complete_remaining_cfs
                        return
                if drain_run.drain_type == DrainType.PAPER_DRAIN or drain_run.drain_type == DrainType.TRANSFER:
                    n = day - drain_run.start_day
                    if n < len(drain_run.paper_drains):
                        tentative = drain_run.paper_drains[n] - evap
                    else:
                        print('fill_mvi_proj paper fill short of values')
                        tentative = -evap
                else:
                    tentative = -self.storable[day] - evap
                if fill_run is not None:
                    pool = self.pool[day]  # Pool is filling and draining at the same time, so use today's filled above
                else:
                    pool = self.pool[day - 1]
                if tentative < pool:
                    self.pool[day] = pool - tentative
                else:
                    if not drain_run.complete_day:
                        remaining = self.storable[day] + pool
                        drain_run.ending(logger, day, remaining)
                    self.pool[day] = 0

        # Accountant unwisely moved US EX into MVI PROJ for these days
        sep4 = WaterYear.day_for_date(dates, 'Sep-04')
        oct9 = WaterYear.day_for_date(dates, 'Oct-09')
        if water_year_info.year == 2023 and sep4 <= day <= oct9:
            self.us_exchange_cfs[day] = 9.44


class MVIProjPool(Pool):
    def __init__(self, pool_name:str, owner_name:str, exl:dict, out:dict, dates, pool_queue_all:PoolQueue):
        super().__init__(pool_name, owner_name)

        self.pool_queue_all = pool_queue_all
        self.pool_queue = self.pool_queue_all.get_runs_for_variable_name('MVI PROJ')

        # Inputs
        self.storable = exl['MVI STORABLE']
        if 'MVI EVAP' in out:
            self.mvi_evap = out['MVI EVAP']
        else:
            self.mvi_evap = exl['MVI STORED EVAP']
        num_days = len(self.mvi_evap)

        #  Outputs
        self.pool = WaterYear.get_out('MVI PROJ', out, num_days)

        self.x = exl

        self.apr1 = WaterYear.day_for_date(dates, 'Apr-1')
        self.oct15 = WaterYear.day_for_date(dates, 'Oct-15')

    def daily_update(self, day:int, date_str:str, pool_queue:PoolQueue, logger:UIAbstraction, event_log:EventLog,
                     exl:dict, inp:dict, out:dict, custom_data:dict, dates:list, water_year_info:WaterYearInfo):

        if day < self.apr1 or day > self.oct15:
            return

        date_str = WaterYearInfo.format_to_month_day(dates[day])
        if date_str == 'Jul-24':
            pass

        fill_run, drain_run, evap_run = pool_queue.get_runs_for_day(day, 'MVI PROJ')

        evap = 0
        if evap_run is not None:
            evap = self.mvi_evap[day-1] / WaterYear.af_to_cfs

        if fill_run is not None:
            if fill_run.fill_type == FillType.PAPER_FILL:
                n = day - fill_run.start_day
                if n < len(fill_run.paper_fills):
                    tentative = fill_run.paper_fills[n] - evap
                else:
                    tentative = 0 - evap
            else:
                tentative = self.storable[day] - evap
            self.pool[day] = self.pool[day - 1] + tentative

        elif drain_run is not None:
            if day == drain_run.start_day:
                # 2025
                # =x['MVI PROJ'][day-1]-(-x['MVI STORABLE'][day]-x['U/S EX'][day-1])
                end_runs:list[DrainRun] = self.pool_queue_all.get_completed_on_day(drain_run.start_day)
                if end_runs:
                    self.pool[day] = self.pool[day-1] + end_runs[0].complete_remaining_cfs
                    return
            if drain_run.drain_type == DrainType.PAPER_DRAIN or drain_run.drain_type == DrainType.TRANSFER:
                n = day - drain_run.start_day
                if n < len(drain_run.paper_drains):
                    tentative = drain_run.paper_drains[n] - evap
                else:
                    print('fill_mvi_proj paper fill short of values')
                    tentative = -evap
            else:
                tentative = -self.storable[day] + evap

            # Accountant unwisely moved US EX into MVI PROJ for these days
            sep4 = WaterYear.day_for_date(dates, 'Sep-04')
            oct1 = WaterYear.day_for_date(dates, 'Oct-01')
            oct9 = WaterYear.day_for_date(dates, 'Oct-09')
            if water_year_info.year == 2023 and sep4 <= day <= oct9 and day != oct1 and day != oct1+1 and day != oct1+2:
                tentative -= 9.44
                if day == sep4:
                    tentative -= self.x['U/S EX'][day-1]

            if tentative < self.pool[day-1]:
                self.pool[day] = self.pool[day - 1] - tentative
            else:
                if not drain_run.complete_day:
                    remaining = self.pool[day] - tentative
                    drain_run.ending(logger, day, remaining)
                self.pool[day] = 0
        else:
            self.pool[day] = self.pool[day-1] - evap