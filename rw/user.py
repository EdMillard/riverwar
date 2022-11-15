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
from rw.util import avg_annual, reshape_annual_range, subtract_annual
from pathlib import Path
from source import usbr_report


class User(object):
    def __init__(self, module, name, state, example=False):
        self.name = name
        self.state = state
        #self.diversion = None
        self.active = False
        self.cu_for_years = None
        self.example = example
        self.factor = None
        self.assessment = None
        if module:
            try:
                self.diversion_func = getattr(module, name + '_diversion')
            except AttributeError:
                print('User ', name, ' has no diversion method')
                self.diversion_func = None
            try:
                self.cu_func = getattr(module, name + '_cu')
            except AttributeError:
                self.cu_func = None
                print('User ', name, ' has no cu method')
            try:
                self.returns_func = getattr(module, name + '_returns')
            except AttributeError:
                self.returns_func = None
                print('User ', name, ' has no returns method')
        else:
            self.diversion_func = None
            self.cu_func = None
            self.returns_func = None

    def make_path(self, file_suffix):
        return Path(self.state + '/usbr_' + self.state + '_' + self.name + file_suffix)

    @staticmethod
    def path_exists(path):
        full_path = Path('data/USBR_Reports/').joinpath(path)
        return full_path.exists()

    def diversion_path(self):
        path = self.make_path('_diversion.csv')
        if User.path_exists(path):
            return path
        else:
            return None

    def diversion(self):
        if self.diversion_func:
            return self.diversion_func()
        else:
            path = self.diversion_path()
            if path:
                return usbr_report.annual_af(path)  # FIXME need water_year_month here
            else:
                print("user diversion file not found: ", path)
                return None

    def cu_path(self):
        path = self.make_path('_consumptive_use.csv')
        if User.path_exists(path):
            return path
        else:
            return None

    def cu(self):
        if self.cu_func:
            return self.cu_func()
        else:
            path = self.cu_path()
            if path:
                return usbr_report.annual_af(path)  # FIXME need water_year_month here
            else:
                returns_path = self.make_path('_returns.csv')
                if User.path_exists(returns_path):
                    print("FIXME User Returns to compute cu: ", self.name)
                else:
                    diversion_path = self.make_path('_diversion.csv')
                    if User.path_exists(diversion_path):
                        return usbr_report.annual_af(diversion_path)
                    else:
                        print("user consumptive use file not found: ", path)
                        return None

    def avg_cu(self):
        return round(avg_annual(self.cu_for_years))

    def returns_path(self):
        path = self.make_path('_returns.csv')
        if User.path_exists(path):
            return path
        else:
            return None

    def returns(self):
        if self.returns_func:
            return self.returns_func()
        else:
            path = self.returns_path()
            if path:
                return usbr_report.annual_af(path)  # FIXME need water_year_month here
            else:
                diversion = self.diversion()
                cu = self.cu()
                if diversion is not None and cu is not None:
                    return subtract_annual(diversion, cu)
                else:
                    print(self.name, "has no returns implementation")

    def get_cu_for_years(self, year_begin, year_end):
        user_cu = self.cu()
        cu_for_years = reshape_annual_range(user_cu, year_begin, year_end)
        for cu in cu_for_years:
            if cu[1] != 0:
                self.cu_for_years = cu_for_years
                return self.cu_for_years

        self.cu_for_years = None
        return None
