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
from rw.user import User
from rw.util import add_annuals, reshape_annual_range

states = {}
current_last_year = 2021


def state_by_abbreviation(abbreviation):
    return states[abbreviation]


class State(object):
    def __init__(self, name, abbreviation, module):
        self.name = name
        self.abbreviation = abbreviation
        self.module = module
        self.users = {}
        self.init = getattr(module, 'init')
        self.init(self)

        states[abbreviation] = self

    def user(self, module, name):
        user = User(module, name)
        self.users[name] = user

    def total_user_diversion(self):
        user_diversions = []
        for key, value in self.users.items():
            user_diversions.append(value.diversion())
        user_diversions[0] = reshape_annual_range(user_diversions[0], 1964, current_last_year)
        return add_annuals(user_diversions)

    def total_user_cu(self):
        user_cus = []
        for key, value in self.users.items():
            user_cus.append(value.cu())
        user_cus[0] = reshape_annual_range(user_cus[0], 1964, current_last_year)
        return add_annuals(user_cus)

    def total_user_returns(self):
        user_returns = []
        for key, value in self.users.items():
            user_returns.append(value.returns())
        user_returns[0] = reshape_annual_range(user_returns[0], 1964, current_last_year)
        return add_annuals(user_returns)
