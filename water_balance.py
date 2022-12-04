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
from basins import lc
from matplotlib import pyplot

if __name__ == '__main__':
    # pyplot.switch_backend('Agg')  # FIXME must be accessing pyplt somewhere
    test_model = lc.Model('test')
    test_model.options.yuma_users_moved_to_reach_4 = True
    test_model.options.crit_in_reach_3a = True
    test_model.options.palo_verde_in_reach_3b = True
    test_model.options.reach6_for_mexico = True
    test_model.options.use_rise_release_data_if_available = True
    test_model.initialize(2016, 2021, water_year_month=1)
    test_model.run(2016, 2021)
    summary = test_model.print()
    summaries = [summary]
    lc.model_run_summaries(1, summaries)

