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
import numpy as np

class TimeSeries:
    sources:dict = {}
    def __init__(self, variable_name:str, source_name:str, source:dict, units:str='',
                 alt_date_time:list[np.datetime64]|None=None):
        self.variable_name:str = variable_name
        self.source_name:str = source_name
        self.source:dict = source
        self.units:str = units
        self.alt_date_time:list[np.datetime64]|None = alt_date_time

    def get_data(self):
        x = None
        y = None
        if self.source is not None:
            x = self.source.get('DATE')
            if x is None:
                print(f'TimeSeries.get_data {self.source_name} \'DATE\' not found')
            y = self.source.get(self.variable_name)
            if y is not None and not isinstance(y, list):
                if len(y.dtype) > 1:
                    x = y['dt']
                    y = y['val']
            else:
                print(f'TimeSeries.get_data {self.source_name} {self.variable_name} not found')
        else:
            print(f'TimeSeries.get_data source {self.source_name} not found')

        return x, y

    def copy(self):
        return copy.copy(self)

    def __str__(self):
        return f'{self.source_name} {self.variable_name} {self.units}'
