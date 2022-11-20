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
    pyplot.switch_backend('Agg')  # FIXME must be accessing pyplt somewhere
    summaries = []
    num_runs = 4
    for run_number in range(0, num_runs):
        snwa_loss_model = lc.Model('snwa_loss_study')
        if run_number == 0:
            pass
        elif run_number == 1:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
        elif run_number == 2:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
            snwa_loss_model.option_grand_canyon_inflow_cancels_mead_evap = True
        elif run_number == 3:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
            snwa_loss_model.option_grand_canyon_inflow_cancels_mead_evap = True
            snwa_loss_model.option_yuma_users_moved_to_reach_4 = True
        elif run_number == 4:
            snwa_loss_model.option_crit_in_reach_3a = True
        elif run_number == 5:
            snwa_loss_model.option_palo_verde_in_reach_3b = True
        else:
            snwa_loss_model.option_havasu_evap_charge_to_havasu_users = True
            snwa_loss_model.option_yuma_users_moved_to_reach_4 = True
            snwa_loss_model.option_grand_canyon_inflow_cancels_mead_evap = True
            snwa_loss_model.option_crit_in_reach_3a = True
            snwa_loss_model.option_palo_verde_in_reach_3b = True

        snwa_loss_model.initialize()
        snwa_loss_model.run(2019, 2021)
        summary = snwa_loss_model.print()
        summaries.append(summary)

    lc.model_run_summaries(num_runs, summaries)
