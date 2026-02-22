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
import copy
from enum import Enum
import numpy as np
from typing import List, Tuple, Any
from source.water_year_info import WaterYearInfo
from api.event_log import EventLog
from api.ui_abstraction import UIAbstraction


class PoolRun:
    def __init__(self, variable_name:str, start_day:int, dates):
        self.variable_name:str = variable_name
        self.start_day:int = start_day
        self.dates = dates
        self.end_day:int = 0
        self.complete_day:int = 0
        self.complete_remaining_cfs:float = 0
        self.still_in_progress:bool = False
        self.paper_start_cfs:float = 0
        self.paper_end_cfs:float = 0

    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        start_date = self.start_date()
        if self.end_day and self.end_day > self.start_day+1:
            end_date = self.end_date_for_print()
            end_str = f"'{end_date}'"
        else:
            end_str = '        '

        string = f" '{start_date}'-{end_str} \'{self.variable_name}\' TYPE"

        if self.complete_day:
            complete_date = self.complete_date()
            string += f" complete '{complete_date}'"

        if self.complete_remaining_cfs > 0:
            string += f' {self.complete_remaining_cfs:6.2f} CFS'

        if self.still_in_progress:
            string += ' still in progress'
        return string

    def num_days(self)->int:
        if self.end_day:
            return self.end_day - self.start_day
        else:
            return 1

    def start_date(self)->str:
        return WaterYearInfo.format_to_month_day(self.dates[self.start_day])

    def end_date(self)->str:
        if self.end_day:
            return WaterYearInfo.format_to_month_day(self.dates[self.end_day])
        return ''

    def end_date_for_print(self)->str:
        if self.end_day:
            return WaterYearInfo.format_to_month_day(self.dates[self.end_day-1])
        return ''

    def complete_date(self)->str:
        if self.complete_day:
            return WaterYearInfo.format_to_month_day(self.dates[self.complete_day])
        return ''

    def ending(self, logger:UIAbstraction, day:int, remaining_cfs:float):
        self.complete_day = day
        self.complete_remaining_cfs = remaining_cfs


class FillType(Enum):
    NONE = 0
    FILL = 1
    PAPER_FILL = 2

    def __str__(self)->str:
        names = {
            self.NONE: "No Fill",
            self.FILL: "",
            self.PAPER_FILL: "Paper Fill",
        }
        return names[self]

class DateValue:
    def __init__(self, start_date:str, value:float):
        self.start_date:str = start_date
        self.value:float = value

    def __str__(self)->str:
        string = f"'{self.start_date}' {self.value:5.3f}"
        return string


class FillRun(PoolRun):
    def __init__(self, variable_name:str, fill_type:FillType, start_day:int, dates:list[str]):
        super().__init__(variable_name, start_day, dates)
        self.fill_type:FillType = fill_type
        self.target:float = 0.0
        self.paper_fills:list[float] = []
        self.paper_fill_dates:list[str] = []
        self.date_values:list[DateValue] = []

    def __str__(self)->str:
        string = super().__str__()
        type_str:str =  str(self.fill_type)
        string = 'Fill  ' + string.replace('TYPE', type_str)
        if self.target:
            string += f' target={self.target:7.3f}'

        if self.date_values:
            for date_value in self.date_values:
                string += f' {str(date_value)}'
        elif self.paper_fills:
            if len(self.paper_fills) == 1:
                string += f': {self.paper_fills[0]:7.3f}'
            else:
                string += f': [0]{self.paper_fills[0]:7.3f}'
                string += f':[{len(self.paper_fills) - 1}]{self.paper_fills[-1]:7.3f}'

        return string

    def append_paper_fill(self, value:float, date:str)->None:
        self.paper_fills.append(value)
        self.paper_fill_dates.append(date)

    def append_date_value(self, start_date:str, value:float)->None:
        self.date_values.append(DateValue(start_date, value))

    def get_value_for_day(self, day:int)->float:
        for date_value in reversed(self.date_values):
            start_day = WaterYearInfo.day_for_date(self.dates, date_value.start_date)
            if day >= start_day:
                return date_value.value
        print(f'get_value_for_day out of range {day} {str(self.date_values)}')
        return 0.0

    def fill_pool(self, pool:list|np.ndarray, call_water:list|np.ndarray):
        day = 0
        end_day = self.end_day
        if not end_day:
            end_day = len(pool)
        for day in range(self.start_day, end_day):
            cfs = PoolQueue.get_value(day, call_water)
            if cfs > 0.0:
                available = self.target - pool[day-1]
                if cfs < available: # Filling
                    pool[day] = pool[day-1] + cfs
                else: # Fill complete
                    self.complete_day = day
                    self.complete_remaining_cfs = cfs - available
                    pool[day] = pool[day-1] + available
                    break
            else:
                pass # Call water is negative so we are draining not filling

        start_day = day + 1
        for day in range(start_day, len(pool)):
            pool[day] = pool[day - 1]


class DrainType(Enum):
    NONE = 0
    DRAIN = 1
    EVAP = 2
    CUSTOM = 3
    TRANSFER = 4
    SPILL = 5
    PAPER_DRAIN = 6

    def __str__(self)->str:
        names = {
            self.NONE: "No Drain",
            self.DRAIN: "",
            self.EVAP: "",
            self.CUSTOM: "Custom Drain",
            self.TRANSFER: "Transfer",
            self.SPILL: "Spill",
            self.PAPER_DRAIN: "Paper Drain",
        }
        return names[self]


class DrainRun(PoolRun):
    def __init__(self, variable_name:str, drain_type:DrainType, start_day:int, dates:list[str]):
        super().__init__(variable_name, start_day, dates)
        self.drain_type:DrainType = drain_type
        self.paper_drains:list[float] = []
        self.paper_drain_dates:list[str] = []
        self.transfer_to:str = ''
        self.overdrafts:list[DateValue] = []

    def __str__(self)->str:
        string = super().__str__()
        type_str:str =  str(self.drain_type)
        string = 'Drain ' + string.replace('TYPE', type_str)
        if self.drain_type == DrainType.PAPER_DRAIN or self.drain_type == DrainType.TRANSFER:
            if self.paper_drains:
                if len(self.paper_drains) == 1:
                    string += f': {self.paper_drains[0]:7.3f}'
                else:
                    string += f': [0]{self.paper_drains[0]:7.3f}'
                    string += f':[{len(self.paper_drains)-1}]{self.paper_drains[-1]:7.3f}'
            if self.transfer_to:
                string += f': transfer_to={self.transfer_to}'
            if self.overdrafts:
                if len(self.overdrafts) == 1:
                    string += f': overdraft {str(self.overdrafts[0])}'
                else:
                    string += f': overdraft {str(self.overdrafts[0])}...{str(self.overdrafts[-1])}'

        return string

    def append_paper_drain(self, value:float, date:str)->None:
        self.paper_drains.append(value)
        self.paper_drain_dates.append(date)


class EvapRun(PoolRun):
    def __init__(self, variable_name:str, start_day:int, dates:list[str]):
        super().__init__(variable_name, start_day, dates)
        self.drain_type:DrainType = DrainType.EVAP

    def __str__(self)->str:
        string = super().__str__()
        type_str:str =  str(self.drain_type)
        return 'Evap ' + string.replace('TYPE', type_str)


class PoolQueue(List):
    af_to_cfs = 1.9835

    def __init__(self, items:list|None=None):
        if items is None:
            items = []
        super().__init__(items)

        self.fill_run:FillRun|None = None
        self.drain_run:DrainRun|None = None
        self.evap_run:EvapRun|None = None

        self.fill_queue:PoolQueue|None = None
        self.drain_queue:PoolQueue|None = None
        self.evap_queue:PoolQueue|None = None

    def get_runs_for_variable_name(self, variable_name:str):
        runs = PoolQueue([])
        for run in self:
            if run.variable_name == variable_name:
                runs.append(run)
        return runs

    def get_completed_on_day(self, end_day:int):
        runs = PoolQueue([])
        for run in self:
            if run.complete_day == end_day:
                if isinstance(run, DrainRun):
                    drain_run:DrainRun = run
                    if drain_run.complete_day == end_day:
                        runs.append(run)
                elif isinstance(run, FillRun):
                    fill_run:FillRun = run
                    if fill_run.complete_day == end_day:
                        runs.append(run)
        return runs

    def get_all_runs_for_day(self, day:int)->list:
        runs = PoolQueue([])
        for run in self:
            if run.start_day <= day < run.end_day:
                runs.append(run)

        return runs

    def get_runs_for_day(self, day:int, variable_name:str):
        fill_run = drain_run = evap_run = None
        for run in self:
            if run.start_day <= day < run.end_day:
                if variable_name == run.variable_name:
                    if isinstance(run, FillRun):
                        if fill_run is None:
                            fill_run = run
                        else:
                            print(f'get_runs_for_day overlapping fill runs {day} {variable_name}')
                    if isinstance(run, DrainRun):
                        if drain_run is None:
                            drain_run = run
                        else:
                            print(f'get_runs_for_day overlapping drain runs {day} {variable_name}')
                    elif isinstance(run, EvapRun):
                        if evap_run is None:
                            evap_run = run
                        else:
                            print(f'get_runs_for_day overlapping evap runs {day} {variable_name}')
        if fill_run is not None and drain_run is not None:
            print(f'get_runs_for_day overlapping fill and drain runs {day} {variable_name}')

        return fill_run, drain_run, evap_run

    def get_first_fill_run(self)->FillRun|None:
        if len(self):
            if isinstance(self[0], FillRun):
                return self.pop(0)
        return None

    def get_fill_runs(self)->list[FillRun]:
        fill_runs:list[FillRun] = []
        if len(self):
            for run in self:
                if isinstance(run, FillRun):
                    fill_runs.append(run)
        return fill_runs

    def get_drain_runs(self)->list[DrainRun]:
        drain_runs:list[DrainRun] = []
        if len(self):
            for run in self:
                if isinstance(run, DrainRun):
                    drain_runs.append(run)
        return drain_runs

    def get_evap_runs(self)->list[EvapRun]:
        evap_runs:list[EvapRun] = []
        if len(self):
            for run in self:
                if isinstance(run, EvapRun):
                    evap_runs.append(run)
        return evap_runs

    def merge_adjacent_fill_runs(self):
        pool_queue = PoolQueue([])

        prev_obj:FillRun | None = None
        for obj in self:
            if prev_obj is not None:
                if prev_obj.variable_name == obj.variable_name:
                    if prev_obj.end_day == obj.start_day:
                        if obj.fill_type == prev_obj.fill_type \
                            or (prev_obj.fill_type == FillType.FILL and obj.fill_type == FillType.PAPER_FILL):
                            print(f'\tmerging {str(prev_obj)} {str(obj)}')
                            prev_obj = prev_obj.copy()
                            prev_obj.end_day = obj.end_day
                            print(f'\t merged {str(prev_obj)}')
                        elif prev_obj.fill_type == FillType.PAPER_FILL and prev_obj.num_days() == 1 and obj.fill_type == FillType.FILL:
                            print(f'\tmerging {str(prev_obj)} {str(obj)}')
                            obj.start_day = prev_obj.start_day
                            obj.paper_start_cfs = prev_obj.paper_fills[0]
                            prev_obj = obj.copy()
                            print(f'\t merged {str(prev_obj)}')
                        else:
                            pool_queue.append(prev_obj)
                            prev_obj = obj
                    else:
                        pool_queue.append(prev_obj)
                        prev_obj = obj
                else:
                    pool_queue.append(prev_obj)
                    prev_obj = obj
            else:
                prev_obj = obj
        if prev_obj is not None:
            pool_queue.append(prev_obj)
        return pool_queue

    def merge_adjacent_drain_runs(self):
        pool_queue = PoolQueue([])

        prev_obj:DrainRun | None = None
        for obj in self:
            if prev_obj is not None:
                if prev_obj.variable_name == obj.variable_name:
                    if obj.variable_name == 'MVI PROJ':
                        pass
                    if prev_obj.end_day == obj.start_day:
                        if isinstance(obj, DrainRun) and isinstance(prev_obj, DrainRun):
                            if obj.drain_type == prev_obj.drain_type:
                                print(f'\tmerging {str(prev_obj)} with: {str(obj)}')
                                prev_drain_obj:DrainRun = prev_obj.copy()
                                if obj.paper_drains:
                                    prev_drain_obj.paper_drains.extend(obj.paper_drains)
                                    prev_drain_obj.paper_drain_dates.extend(obj.paper_drain_dates)
                                prev_drain_obj.end_day = obj.end_day
                                prev_obj = prev_drain_obj
                                print(f'\t merged {str(prev_obj)}')
                            elif prev_obj.drain_type == DrainType.PAPER_DRAIN and prev_obj.num_days()==1 and obj.drain_type == DrainType.DRAIN:
                                print(f'\tmerging {str(prev_obj)} with: {str(obj)}')
                                prev_obj = obj.copy()
                                prev_obj.start_day = obj.start_day - 1
                                print(f'\t merged {str(prev_obj)}')
                            else:
                                pool_queue.append(prev_obj)
                                prev_obj = obj
                        else:
                            pool_queue.append(prev_obj)
                            prev_obj = obj
                    else:
                        pool_queue.append(prev_obj)
                        prev_obj = obj
                else:
                    pool_queue.append(prev_obj)
                    prev_obj = obj
            else:
                prev_obj = obj
        if prev_obj is not None:
            pool_queue.append(prev_obj)
        return pool_queue

    def merge_adjacent_evap_runs(self):
        pool_queue = PoolQueue([])

        prev_obj:EvapRun | None = None
        for obj in self:
            if prev_obj is not None:
                if prev_obj.variable_name == obj.variable_name:
                    if prev_obj.end_day == obj.start_day:
                        if isinstance(obj, EvapRun) and isinstance(prev_obj, EvapRun):
                            print(f'\tmerging {str(prev_obj)} {str(obj)}')
                            prev_obj = prev_obj.copy()
                            prev_obj.end_day = obj.end_day
                            print(f'\t merged {str(prev_obj)}')
                        else:
                            pool_queue.append(prev_obj)
                            prev_obj = obj
                    else:
                        pool_queue.append(prev_obj)
                        prev_obj = obj
                else:
                    pool_queue.append(prev_obj)
                    prev_obj = obj
            else:
                prev_obj = obj
        if prev_obj is not None:
            pool_queue.append(prev_obj)
        return pool_queue

    def dequeue_pool_return_last(self, variable_name:str):
        last_pool_obj = None

        for obj in self:
            if obj.variable_name == variable_name:
                last_pool_obj = obj

        if last_pool_obj is not None:
            pool_queue = PoolQueue([])
            for obj in self:
                if obj.variable_name != variable_name:
                    pool_queue.append(obj)
                elif obj.variable_name == variable_name and obj is last_pool_obj:
                    pool_queue.append(obj)
        else:
            pool_queue = PoolQueue(self)

        return pool_queue, last_pool_obj

    def build_pool_runs(self, logger, variable_name:str, fill_values, drain_values, spill_values, config:dict,
                        fill_drain_variable_names:list[str], evap_variable_names:list[str], evap_values,
                        equations:dict, data:dict, dates:list[str], allow_transfers:bool=False,
                        fill_max_end_date:str|None=None, transfer_to_names:list[str]|None=None,
                        do_paper_drains:bool=False):
        f = equations.get(variable_name)
        d = data.get(variable_name)
        pool_values = data.get(variable_name)
        if not f or not d or pool_values is None or fill_values is None or drain_values is None or evap_values is None:
            logger.log_message(f'Build Pool Runs for {variable_name} failed')
            return None, None, None

        day_runs = PoolQueue.find_string_runs(f)
        fill_drain_runs = PoolQueue.find_directional_runs(d, day_runs)
        date_runs = PoolQueue.day_runs_with_string_to_date_string_runs(fill_drain_runs, dates)

        fill_runs = []
        drain_runs = []
        evap_runs = []

        self.fill_queue:PoolQueue = PoolQueue([])
        self.drain_queue:PoolQueue = PoolQueue([])
        self.evap_queue:PoolQueue = PoolQueue([])

        for run in date_runs:
            if run[2] == 'fill':
                run = run[:2]
                fill_runs.append(run)
            elif run[2] == 'drain':
                run = run[:2]
                drain_runs.append(run)

        custom_runs = []
        custom_start_day = -1
        custom = False

        fill_max_end_day = len(dates)
        if fill_max_end_date:
            fill_max_end_day = WaterYearInfo.day_for_date(dates, fill_max_end_date)

        day = 0
        for day, equation in enumerate(f):
            date_str = WaterYearInfo.format_to_month_day(dates[day])

            paper_fill = 0

            pool_delta = PoolQueue.get_delta(day, pool_values)
            pool = PoolQueue.get_value(day, pool_values)
            fill_value = PoolQueue.get_value(day, fill_values)
            drain_value = PoolQueue.get_value(day, drain_values)
            spill_value = PoolQueue.get_value(day, spill_values)

            if day > 0:
                evap_value = PoolQueue.get_value(day-1, evap_values)
            else:
                evap_value = 0.0
            evap_delta = 0.0 - evap_value
            evap_delta /= PoolQueue.af_to_cfs

            if variable_name == 'MVI PROJ':
                if date_str == 'Sep-04':
                    pass

            if pool == 0.0:
                # If pool is drained, can't drain anymore
                self.end_drain_run(variable_name, day, date_str)
            elif pool < 0:
                # Except you can overdraft a pool due to accounting errors
                # print(f'  {date_str} {variable_name} overdrafting pool {pool}')
                pass
            if drain_value == 0.0:
                self.end_evap_run(variable_name, day, date_str)

            if equation is not None:
                # Fill/Drain analysis
                #
                equation_may_be_nulled = False
                if '*0)' in equation or equation.endswith('*0'):
                    print(f'  {date_str} {variable_name} equation may be nulled: {equation}')
                    equation_may_be_nulled = True

                fill_drain_names_in_equation = PoolQueue.variable_names_in_equation(fill_drain_variable_names, equation)
                evap_names_in_equation = PoolQueue.variable_names_in_equation(evap_variable_names, equation)
                transfer_to_names_in_equation = []
                if transfer_to_names:
                    transfer_to_names_in_equation = PoolQueue.variable_names_in_equation(transfer_to_names, equation)

                if fill_drain_names_in_equation and not equation_may_be_nulled:
                    if fill_value > 0 and pool_delta > 0:
                        # Filling something on this day
                        self.end_drain_run(variable_name, day, date_str)
                        if np.isclose(fill_value, pool_delta, atol=0.0001) \
                        or np.isclose(fill_value + evap_delta, pool_delta, atol=0.0001):
                            if self.fill_run and self.fill_run.fill_type != FillType.FILL:
                                self.end_fill_run(variable_name, day, date_str)
                            if not self.fill_run and day <= fill_max_end_day:
                                self.fill_run = FillRun(variable_name, FillType.FILL, day, dates)
                        else:
                            if self.fill_run and self.fill_run.fill_type != FillType.PAPER_FILL:
                                self.end_fill_run(variable_name, day, date_str)
                            if not self.fill_run:
                                self.fill_run = FillRun(variable_name, FillType.PAPER_FILL, day, dates)
                            self.fill_run.append_paper_fill(pool_delta, date_str)
                    elif drain_value < 0 and pool_delta < 0:
                        # Draining something on this day
                        self.end_fill_run(variable_name, day, date_str)
                        if np.isclose(evap_delta, pool_delta, atol=0.0001):
                            # evap
                            pass
                        elif np.isclose(drain_value, pool_delta, atol=0.0001) \
                        or np.isclose(evap_delta+drain_value, pool_delta, atol=0.0001):
                            if not self.drain_run or self.drain_run.drain_type != DrainType.DRAIN:
                                self.end_drain_run(variable_name, day, date_str)
                                self.drain_run = DrainRun(variable_name,  DrainType.DRAIN, day, dates)
                        else:
                            # Must be a custom drain
                            if allow_transfers:
                                self.is_drain_transfer(variable_name, day, date_str, dates, pool_delta, transfer_to_names_in_equation)
                            elif not self.drain_run or self.drain_run.drain_type != DrainType.DRAIN:
                                self.end_drain_run(variable_name, day, date_str)
                                self.drain_run = DrainRun(variable_name,  DrainType.DRAIN, day, dates)
                    elif drain_value > 0 > pool_delta:
                        # Pool is draining while call water is available, either evap or a transfer between pools
                        if np.isclose(evap_delta, pool_delta, atol=0.0001):
                            # evap, handled below hopefully
                            pass
                        elif np.isclose(-spill_value, pool_delta, atol=0.0001):
                            self.end_fill_drain_runs(variable_name, day, date_str)
                            if not self.drain_run:
                                self.drain_run = DrainRun(variable_name, DrainType.DRAIN, day, dates)
                        else:
                            if pool < 0:
                                if self.drain_run:
                                    self.drain_run.overdrafts.append(DateValue(date_str, pool))
                            if allow_transfers:
                                self.is_drain_transfer(variable_name, day, date_str, dates, pool_delta, transfer_to_names_in_equation)
                            elif not self.drain_run:
                                self.end_fill_drain_runs(variable_name, day, date_str)
                                self.drain_run = DrainRun(variable_name,  DrainType.DRAIN, day, dates)
                            if pool < 0:
                                if self.drain_run:
                                    self.drain_run.overdrafts.append(DateValue(date_str, pool))
                    elif fill_value == 0 and pool_delta == 0:
                        # No change today
                        self.end_all_runs(variable_name, day, date_str)
                    else:
                        # Evap or change isn't on this variable
                        self.end_fill_drain_runs(variable_name, day, date_str)

                elif pool_delta == 0.0:
                    # No change today
                    self.end_all_runs(variable_name, day, date_str)
                elif pool_delta > 0.0:
                    # Something changed, but it wasn't from storable/call water parameter
                    # It might be a paper fill, might be a remainder from a just ended fill
                    self.end_drain_run(variable_name, day, date_str)
                    if self.fill_run:
                        if self.fill_run.fill_type != FillType.PAPER_FILL:
                            self.end_fill_run(variable_name, day, date_str)
                            self.fill_run = None
                    if not self.fill_run:
                        self.fill_run = FillRun(variable_name, FillType.PAPER_FILL, day, dates)
                    self.fill_run.append_paper_fill(pool_delta, date_str)
                elif pool_delta < 0.0:
                    # Something changed, but it wasn't from storable/call water parameter
                    # Probably evap, might be a remainder from a just ended drain
                    if self.fill_run:
                        self.end_fill_run(variable_name, day, date_str)
                        self.fill_run = None
                    if np.isclose(evap_delta, pool_delta, atol=0.0001):
                        # evap
                        if self.drain_run:
                            self.end_drain_run(variable_name, day, date_str)
                    elif np.isclose(drain_value + evap_delta, pool_delta, atol=0.0001):
                        # evap and drain
                        pass
                    else:
                        if do_paper_drains:
                            self.start_paper_drain(variable_name, day, date_str, dates, pool_delta)
                else:
                    self.end_fill_drain_runs(variable_name, day, date_str)

                # Evap analysr w
                if evap_names_in_equation and pool != 0.0 and (evap_value != 0 or day == 0):
                    if np.isclose(evap_delta, pool_delta, atol=0.0001) or paper_fill > 0:
                        # print(f'  {date_str} {variable_name} {day} evap {evap_delta:4.2f} only')
                        if not self.evap_run and pool > 0:
                            self.evap_run = EvapRun(variable_name, day, dates)
                    elif np.isclose(evap_delta+drain_value, pool_delta, atol=0.0001) or paper_fill > 0:
                        if not self.evap_run and pool > 0:
                            self.evap_run = EvapRun(variable_name, day, dates)
                    elif evap_delta < 0:
                        if not self.evap_run and pool > 0:
                            self.evap_run = EvapRun(variable_name, day, dates)
                    else:
                        if pool > 0:
                            self.end_evap_run(variable_name, day, date_str)
                        else:
                            pass # overdraft
                else:
                    self.end_evap_run(variable_name, day, date_str)
            else:
                # No equation, custom data value probably
                data_value = PoolQueue.get_value(day, d)
                if np.isnan(data_value):
                    if pool_delta < 0:
                        if self.fill_run:
                            self.end_fill_run(variable_name, day, date_str)
                        # Accountant abruptly blanked out column with water in pool, i.e. NARR IN MCPHEE spill in 2023
                        self.start_paper_drain(variable_name, day, date_str,  dates, pool_delta)
                    else:
                        self.end_all_runs(variable_name, day, date_str)
                elif data_value == 0.0:
                    pass
                else:
                    pass
                if custom:
                    # print(f'  {date_str} {variable_name} Custom run ends')
                    custom = False
                    if custom_start_day != -1:
                        custom_runs.append((custom_start_day, day))
                        custom_start_day = -1
                self.end_evap_run(variable_name, day, date_str)

        date_str = WaterYearInfo.format_to_month_day(dates[day-1])
        if self.fill_run:
            self.fill_run.still_in_progress = True
            self.end_fill_run(variable_name, day, date_str)
        if self.drain_run:
            self.drain_run.still_in_progress = True
            self.end_drain_run(variable_name, day, date_str)
        if self.evap_run:
            self.evap_run.still_in_progress = True
            self.end_evap_run(variable_name, day, date_str)

        if custom_start_day != -1:
            date_str = WaterYearInfo.format_to_month_day(dates[day-1])
            print(f'  {date_str} {variable_name} custom data in progress')
            custom_runs.append((custom_start_day, day))
        if custom_runs:
            custom_runs = PoolQueue.day_runs_with_string_to_date_string_runs(custom_runs, dates)
        config[variable_name] = (fill_runs, drain_runs, evap_runs, custom_runs)

        if self.fill_queue:
            self.fill_queue = self.fill_queue.merge_adjacent_fill_runs()
            # print('Fill queue:')
            # for fill_run in self.fill_queue:
            #    print(f'  {fill_run}')
        if self.drain_queue:
            self.drain_queue = self.drain_queue.merge_adjacent_drain_runs()
            # print('Drain queue:')
            # for drain_run in self.drain_queue:
            #     print(f'  {drain_run}')
        if self.evap_queue:
            self.evap_queue = self.evap_queue.merge_adjacent_evap_runs()
            # print('Evap queue:')
            # for evap_run in self.evap_queue:
            #     print(f'  {evap_run}')
        return self.fill_queue, self.drain_queue, self.evap_queue

    def start_paper_drain(self, variable_name:str, day:int, date_str:str, dates, pool_delta:float):
        if self.drain_run:
            if self.drain_run.drain_type != DrainType.PAPER_DRAIN:
                self.end_drain_run(variable_name, day, date_str)
                self.drain_run = None
        if not self.drain_run:
            self.drain_run = DrainRun(variable_name, DrainType.PAPER_DRAIN, day, dates)
        self.drain_run.append_paper_drain(pool_delta, date_str)

    def is_drain_transfer(self, variable_name, day, date_str, dates, pool_delta, transfer_to_names_in_equation):
        self.end_fill_run(variable_name, day, date_str)
        if self.drain_run:
            if self.drain_run.drain_type != DrainType.TRANSFER:
                self.end_drain_run(variable_name, day, date_str)
        if not self.drain_run:
            self.drain_run = DrainRun(variable_name, DrainType.TRANSFER, day, dates)
            if transfer_to_names_in_equation:
                self.drain_run.transfer_to = transfer_to_names_in_equation[0]
        self.drain_run.append_paper_drain(pool_delta, date_str)

    def end_fill_run(self, variable_name:str, day:int, date_str:str):
        if self.fill_run:
            if isinstance(self.fill_run, FillRun):
                self.fill_run.end_day = day
                self.fill_queue.append(self.fill_run)
                # print(f'  {date_str} {variable_name} ended {self.fill_run}')
            else:
                print(f"end_fill_run run isn't a FillRun", {variable_name})
            self.fill_run = None

    def end_drain_run(self, variable_name:str, day:int, date_str:str):
        if self.drain_run:
            if isinstance(self.drain_run, DrainRun):
                self.drain_run.end_day = day
                self.drain_queue.append(self.drain_run)
                # print(f'  {date_str} {variable_name} ended {self.drain_run}')
            else:
                print(f"end_drain_run run isn't a DrainRun", {variable_name})
            self.drain_run = None

    def end_evap_run(self, variable_name:str, day:int, date_str:str):
        if self.evap_run:
            if isinstance(self.evap_run, EvapRun):
                self.evap_run.end_day = day
                self.evap_queue.append(self.evap_run)
                # print(f'  {date_str} {variable_name} ended {self.evap_run}')
            else:
                print(f"end_evap_run run isn't a EvapRun", {variable_name})
            self.evap_run = None

    def end_all_runs(self, variable_name:str, day:int, date_str:str):
        self.end_fill_run(variable_name, day, date_str)
        self.end_drain_run(variable_name, day, date_str)
        self.end_evap_run(variable_name, day, date_str)

    def end_fill_drain_runs(self, variable_name:str, day:int, date_str:str):
        self.end_fill_run(variable_name, day, date_str)
        self.end_drain_run(variable_name, day, date_str)

    @staticmethod
    def variable_names_in_equation(variable_names, equation):
        variable_names_in_equation = []
        for variable_name in variable_names:
            if variable_name in equation:
                variable_names_in_equation.append(variable_name)
        return variable_names_in_equation

    @staticmethod
    def analyze_drain_runs(variable_name, drain_variable_names, evap_variable_names, drain_runs, equations, dates):
        result = []
        f = equations.get(variable_name)
        for drain_run in drain_runs:
            start_day = WaterYearInfo.day_for_date(dates, drain_run[0])
            end_day = WaterYearInfo.day_for_date(dates, drain_run[1])

            # print(f'  {variable_name} Drain [{drain_run[0]} {drain_run[1]}]:')
            run = DrainRun(variable_name, DrainType.NONE, start_day, dates)
            for day in range(start_day, end_day+1):
                equation = f[day]
                drain = False
                evap = False
                if equation is not None:
                    for drain_variable_name in drain_variable_names:
                        if drain_variable_name in equation:
                            drain = True
                            break
                    for evap_variable_name in evap_variable_names:
                        if evap_variable_name in equation:
                            evap = True
                            break

                    if drain:
                        drain_state = DrainType.DRAIN
                    elif evap:
                        drain_state = DrainType.EVAP
                    else:
                        drain_state = DrainType.CUSTOM
                    if drain_state != run.drain_type:
                        if run.drain_type != DrainType.NONE:
                            run.end_day = day
                            result.append(run)
                            run = DrainRun(variable_name, drain_state, day, dates)
                        else:
                            run.drain_type = drain_state

                if day == end_day:
                    if day != run.start_day:
                        run.end_day = day
                        result.append(run)
        return result

    def extract_fill_runs_of_type(self, fill_type:FillType):
        runs = []
        for run in self:
            if run.fill_type == fill_type:
                runs.append(run)
        self[:] = [obj for obj in self if obj.fill_type != fill_type]
        return runs

    @staticmethod
    def build_pool_queue(logger, runs, queue_type:str):
        pool_queue = PoolQueue([])
        for key, runs in runs.items():
            # filtered_runs = [obj for obj in runs if obj.drain_type != DrainType.EVAP]
            pool_queue.extend(runs)
        # pool_queue.sort(key=lambda x: x.variable_name)
        pool_queue.sort(key=lambda x: x.start_day)

        logger.log_message(f'  {queue_type} queue')
        for run in pool_queue:
            logger.log_message(f'    {run}')

        return pool_queue

    @staticmethod
    def get_value(day:int, variables:list)->float|int:
        value = 0.0
        if variables is not None and 0 <= day < len(variables):
            if not np.isnan(value):
                value = variables[day]
                if value is None:
                    value = 0.0
            else:
                print(f'get_value [{day}] is nan')
        elif variables is None:
            pass
        else:
            print(f'get_value day {day} out of bounds')

        return value

    @staticmethod
    def get_value_by_name(day:int, variable_name:str, variables)->float|int:
        value = 0.0
        variable = variables.get(variable_name)
        if variable:
            if 0 <= day < len(variable):
                if not np.isnan(value):
                    value = variable[day]
                    if value is None:
                        value = 0.0
                else:
                    print(f'get_value_by_name {variable_name}[{day}] is nan')
            else:
                print(f'get_value_by_name day {day} out of bounds \'{variable_name}\'')
        else:
            print(f'get_value_by_name variable \'{variable_name}\' not found ')

        return value

    @staticmethod
    def get_delta(day:int, variable)->float|int:
        delta = 0
        if day > 0:
            if not np.isnan(variable[day]) and not np.isnan(variable[day-1]):
                delta = variable[day] - variable[day - 1]
            elif not np.isnan(variable[day]):
                delta = variable[day]
            elif not np.isnan(variable[day-1]):
                delta = 0 - variable[day-1]
            # else:
            #    print(f'get_delta [{day}] isnan {variable[day-1]} {variable[day]}')
        else:
            if variable[0] and not np.isnan(variable[0]):
                delta = variable[0]
            # else:
            #    print(f'get_delta [{0}] isnan or none {variable[0]}')
        return delta

    @staticmethod
    def find_string_runs(lst):
        """
        Given a list with strings and None values, returns a list of tuples
        containing (start_index, end_index) for each consecutive run of strings.

        Args:
            lst: List containing strings and None values

        Returns:
            List of tuples (start, end) where each tuple represents a run of strings
            (inclusive indices)

        Example:
            find_string_runs(['a', 'b', None, 'c', None, None, 'd', 'e', 'f'])
            [(0, 1), (3, 3), (6, 8)]
        """
        runs = []
        n = len(lst)
        i = 0

        while i < n:
            # Skip over None values
            while i < n and lst[i] is None:
                i += 1

            if i == n:
                break

            # Found start of a string run
            start = i
            while i < n and lst[i] is not None:
                i += 1

            # Now at the end (exclusive) of the run
            end = i - 1
            runs.append((start, end))

        return runs

    @staticmethod
    def day_runs_with_string_to_date_string_runs(runs, date_times):
        """
        Convert index-based runs to date strings in 'Mon-D' format.

        Args:
            runs: List of tuples (start_idx, end_idx) from string runs
            date_times: List of datetime objects corresponding to original indices

        Returns:
            List of tuples ('start_date_str', 'end_date_str') in 'Nov-1' format
        """
        result = []
        for run in runs:
            start_dt = date_times[run[0]]
            end_dt = date_times[run[1]]

            # Format as 'Nov-1', 'Dec-25', etc.
            start_str = start_dt.strftime('%b-%-d').replace(' 0', ' ')  # Handle single-digit days
            end_str = end_dt.strftime('%b-%-d').replace(' 0', ' ')

            if len(run) == 2:
                result.append((start_str, end_str))
            elif len(run) == 3:
                result.append((start_str, end_str, run[2]))
            else:
                print(f'Invalid day run: {run}')

        return result


    @staticmethod
    def find_directional_runs(
            data: np.ndarray,
            runs: List[Tuple[int, int]]
    ) -> List[Tuple[int, int, str]]:
        result: List[Tuple[int, int, str]] = []

        prev_value = 0
        prev_direction = ''
        start_day = -1
        for run in runs:
            day = run[0]
            for day in range(run[0], run[1]+1):
                value = data[day]
                delta = value - prev_value
                if delta > 0:
                    direction = 'fill'
                elif delta < 0:
                    direction = 'drain'
                else:
                    direction = ''
                if prev_direction != direction:
                    if start_day != -1 and prev_direction:
                        result.append((start_day, day, prev_direction))
                    if direction:
                        start_day = day
                    prev_direction = direction
                prev_value = value
            if start_day != -1 and prev_direction:
                result.append((start_day, day, prev_direction))

        return result


    @staticmethod
    def find_gap_nonzero_runs(
            runs: List[Tuple[int, int]],
            data: List[Any]
    ) -> Tuple[List[Tuple[int, int]], List[float]]:
        # Currently unused
        """
        Given:
            runs – list of (start, end) index pairs from find_string_runs (string runs)
            data – list/array of same length, containing numbers, None, NaN, 0

        Returns:
            gap_runs   – list of (start, end) for runs of non-zero/non-NaN/non-None values
                         **only in the gaps between the given runs**
            cleaned_data – new list with all 0/None/NaN replaced by 0.0, others unchanged
        """
        arr = np.asarray(data, dtype=float)  # None → np.nan
        n = len(arr)

        # Mask: True if value is valid (not 0, not NaN, not None)
        valid_mask = ~np.isnan(arr) & (arr != 0.0)

        # Build mask of positions that are INSIDE the given runs
        in_run_mask = np.zeros(n, dtype=bool)
        for start, end in runs:
            in_run_mask[start:end + 1] = True

        # We only care about valid values OUTSIDE the runs
        gap_valid_mask = valid_mask & ~in_run_mask

        # Find contiguous runs in the gap_valid_mask
        gap_runs: List[Tuple[int, int]] = []
        i = 0
        while i < n:
            if not gap_valid_mask[i]:
                i += 1
                continue

            start = i
            while i < n and gap_valid_mask[i]:
                i += 1
            end = i - 1
            gap_runs.append((start, end))

        # Clean data: keep valid values, zero out everything else
        cleaned_data = np.where(valid_mask, arr, 0.0).tolist()

        return gap_runs, cleaned_data

class Pool:
    def __init__(self, pool_name:str, owner_name:str):
        self.pool_name:str = pool_name
        self.owner_name:str = owner_name

    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f' {self.pool_name} {self.owner_name}'
        return string

    def analyze(self):
        # override
        pass

    def daily_update(self, day:int, date_str:str, pool_queue:PoolQueue, logger:UIAbstraction, event_log:EventLog,
                     exl:dict, inp:dict, out:dict, custom_data:dict, dates:list, water_year_info:WaterYearInfo):
        # override
        pass
