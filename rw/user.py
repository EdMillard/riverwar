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
from rw.util import reshape_annual_range

class User(object):
    def __init__(self, module, name, state):
        self.name = name
        self.state = state
        self.active = False
        self.cu_for_years = None
        try:
            self.diversion = getattr(module, name + '_diversion')
        except AttributeError:
            print('User ', name, ' has no diversion method')
        try:
            self.returns = getattr(module, name + '_returns')
        except AttributeError:
            print('User ', name, ' has no returns method')
        try:
            self.cu = getattr(module, name + '_cu')
        except AttributeError:
            print('User ', name, ' has no cu method')

    def get_cu_for_years(self, year_begin, year_end):
        user_cu = self.cu()
        cu_for_years = reshape_annual_range(user_cu, year_begin, year_end)
        for cu in cu_for_years:
            if cu[1] != 0:
                self.cu_for_years = cu_for_years
                return self.cu_for_years

        self.cu_for_years = None
        return None
