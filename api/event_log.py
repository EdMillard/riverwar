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
import pandas as pd
from source.water_year_info import WaterYearInfo

class EventLog:
    log_inflows = False
    log_outflows = False
    log_flow_max = False
    log_fills = True
    log_drains = True

    af_to_cfs = 1.9835

    def __init__(self):
        self.events = []

    def start_log(self):
        self.events.clear()

    def log(self, day, variable_name, message, is_ending=False):
        self.events.append((day, variable_name, message, is_ending))
        pass

    def log_flow(self, variable_name, flow_dict):
        if variable_name in flow_dict:
            flow_cfs = np.nan_to_num(flow_dict[variable_name])
            num_days = len(flow_cfs)

            if EventLog.log_flow_max:
                max_value = np.max(flow_cfs)  # 9
                max_index_flat = np.argmax(flow_cfs)
                self.log(max_index_flat, variable_name, f'Max    flow {max_value:7.2f} cfs')

            start_indices = EventLog.indices_nonzero_after_zero(flow_cfs)
            end_indices = EventLog.indices_zero_after_nonzero(flow_cfs)
            if len(end_indices) < len(start_indices):
                end_indices = np.append(end_indices, num_days-1)
            elif len(end_indices) > len(start_indices):
                start_indices = np.insert(start_indices, 0, 0)
            elif len(end_indices) and len(start_indices) and end_indices[0] < start_indices[0]:
                start_indices = np.insert(start_indices, 0, 0)
                end_indices = np.append(end_indices, num_days-1)
            elif not len(end_indices) and not len(start_indices):
                start_indices = np.array([0])
                end_indices  = np.array([num_days-1])
            elif len(end_indices) and not len(start_indices):
                pass
            elif not len(end_indices) and len(start_indices):
                pass

            sums_cfs = EventLog.sums_for_flows(start_indices, end_indices, flow_cfs)

            for start_index in start_indices:
                self.log(start_index, variable_name, f'Start  flow {flow_cfs[start_index]:7.2f} cfs')

            for end_index, sum_cfs in zip(end_indices, sums_cfs):
                sum_af = sum_cfs * EventLog.af_to_cfs
                self.log(end_index, variable_name, f'Ending flow {flow_cfs[end_index-1]:7.2f} cfs Subtotal {sum_af:7.2f} af', is_ending=True)
        else:
            print(f'log_flow {variable_name} not found')

    def print_log(self, file_path, dates):
        with open(file_path, "w") as file:
            sorted_events = EventLog.sort_by_int(self.events)
            for event in sorted_events:
                day = event[0]
                if day >= len(dates):
                    day = len(dates) - 1
                try:
                    date_str = WaterYearInfo.format_to_month_day(dates[day])
                    variable_name = f"'{event[1]}'"
                    file.write(f'\'{date_str}\' {variable_name:27} {event[2]}\n')
                except (IndexError, ValueError) as e:
                    print(f'Invalid event: {event} {e}')

    @staticmethod
    def indices_nonzero_after_zero(arr):
        if len(arr) < 2:
            return np.array([], dtype=np.int64)

        # Shifted versions: previous and current elements
        prev = arr[:-1]
        curr = arr[1:]

        mask = (prev == 0) & (curr != 0)

        # Indices offset by +1 since we sliced off the first element
        indices = np.where(mask)[0] + 1

        return indices

    @staticmethod
    def indices_zero_after_nonzero(arr):
        if len(arr) < 2:
            return np.array([], dtype=np.int64)

        # Shifted versions: previous and current elements
        prev = arr[:-1]
        curr = arr[1:]

        # Mask where prev!=0 and curr==0
        mask = (prev != 0) & (curr == 0)

        # Indices offset by +1 since we sliced the first element
        indices = np.where(mask)[0] + 1

        return indices

    @staticmethod
    def sort_by_int(list_of_tuples):
        #def int_key(arr):
        #    int_val = arr[0]
        #    is_ending = arr[3]
        #    if not isinstance(int_val, (int, np.integer)):
        #        raise TypeError(f"First element must be int, got {type(int_val)}")
        #    return int_val  # Directly comparable
        # return sorted(list_of_tuples, key=int_key)

        return sorted(list_of_tuples, key=lambda tup: (tup[0], not tup[3]))

    @staticmethod
    def sums_for_flows(arr1, arr2, variables):
        len1, len2 = len(arr1), len(arr2)

        # Rule 1: Second array shorter than first -> return None immediately
        if len2 < len1:
            return None

        # Now iterate (we know len2 >= len1)
        sums = []
        for i, elem1 in enumerate(arr1):
            # Rule 2: First array shorter than second -> return None on first iter
            if len1 < len2:
                if i == 0:  # First iteration
                    return None
                # (Unreachable if len1 < len2 and we return above, but kept for clarity)

            elem2 = arr2[i]  # Safe: i < len1 <= len2
            sums.append(np.sum(variables[elem1:elem2]))
        return sums