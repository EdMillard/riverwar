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

class Reservoir:
    def __init__(self, name:str):
        self.name:str = name

    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f" '\'{self.name}\'"

        return string

    @staticmethod
    def clip_array_by_dates(arr, start_date, end_date):
        # Ensure start_date and end_date are datetime64
        start_date = np.datetime64(start_date)
        end_date = np.datetime64(end_date)

        dates = arr['dt'].astype('datetime64[D]')
        # Create mask for dates within the range (inclusive)
        mask = (dates >= start_date) & (dates <= end_date)

        # Return clipped array
        return arr[mask]

