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
    def __init__(self, name, water_year_month):
        self.name = name
        self.water_year_month = water_year_month

    def inflow(self, year_begin, year_end):
        return annual_zeroed_for_years(year_begin, year_end)

    def release(self, year_begin, year_end):
        return annual_zeroed_for_years(year_begin, year_end)

    def storage(self):
        print("FIXME Lake.storage() not implemented")
        pass

    def ___convert_to_datetime(self, d):
        return datetime.strptime(np.datetime_as_string(d, unit='s'), '%Y-%m-%dT%H:%M:%S')

    def storage_delta(self, year_begin, year_end):
        delta = []
        date_time_format = "%Y-%m-%d"
        daily_storage = self.storage()
        if daily_storage is not None:
            for year in range(year_begin, year_end+1):
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
            print(self.name + " storage delta not implemented")
            for year in range(year_begin, year_end+1):
                delta.append(0)
        return delta

    def evaporation(self, year_begin, year_end):
        return annual_zeroed_for_years(year_begin, year_end)
