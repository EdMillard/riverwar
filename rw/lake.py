"""
Copyright (c) 2022 Ed Millard

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
from datetime import datetime
import numpy as np
from rw.util import annual_zeroed_for_years


class Lake(object):
    lakes = {}
    year_begin = None
    year_end = None
    water_year_month = 1

    def __init__(self, name):
        Lake.lakes[name] = self
        self.name = name

    def inflow(self):
        return annual_zeroed_for_years(Lake.year_begin, Lake.year_end)

    def side_inflow(self):
        return None

    def release(self):
        return annual_zeroed_for_years(Lake.year_begin, Lake.year_end)

    def bypass(self):
        return None

    def storage(self):
        return None

    @staticmethod
    def lake_by_name(name):
        return Lake.lakes[name]

    @staticmethod
    def ___convert_to_datetime(d):
        return datetime.strptime(np.datetime_as_string(d, unit='s'), '%Y-%m-%dT%H:%M:%S')

    def storage_delta(self):
        delta = []
        date_time_format = "%Y-%m-%d"
        daily_storage = self.storage()
        if daily_storage is not None:
            for year in range(Lake.year_begin, Lake.year_end+1):
                storage_begin = None
                storage_end = None
                water_year_month_str = '-' + str(self.water_year_month) + '-'
                date_begin = datetime.strptime(str(year) + water_year_month_str + '1', date_time_format).date()
                date_end = datetime.strptime(str(year+1) + water_year_month_str + '1', date_time_format).date()
                for l in daily_storage:
                    date = self.___convert_to_datetime(l[0]).date()
                    if date == date_begin:
                        storage_begin = l[1]
                    elif date == date_end:
                        storage_end = l[1]
                        break
                if storage_begin and storage_end:
                    delta.append(storage_end - storage_begin)
                else:
                    print(self.name, 'storage_delta failed')
        else:
            # print(self.name + " storage delta not implemented")
            for year in range(Lake.year_begin, Lake.year_end+1):
                delta.append(0)
        return delta

    def evaporation(self):
        return None
